from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Protocol

from elis_procurement_v2.application.invoice_processor import process_invoice


class BlobStoragePort(Protocol):
    container_processed: str | None

    def list_pdfs(self) -> list[str]: ...

    def blob_exists(self, container_name: str, blob_name: str) -> bool: ...

    def download_pdf(self, blob_name: str) -> bytes: ...

    def upload_json(
        self,
        container_name: str,
        blob_name: str,
        data: dict[str, Any],
    ) -> None: ...


class AnalyzerPort(Protocol):
    analyzer_id: str

    def start_analysis(self, pdf_bytes: bytes) -> str: ...

    def get_analysis_result(self, operation_url: str) -> dict[str, Any]: ...


class OperationStoragePort(Protocol):
    def load(self) -> dict[str, dict[str, str]]: ...

    def save(self, operations: dict[str, dict[str, str]]) -> None: ...


@dataclass
class BatchSummary:
    total_pdfs: int
    already_processed: int
    pending: int
    selected: int
    recoverable: int
    processed: int = 0
    timed_out: int = 0
    failed: int = 0


class BatchProcessor:
    def __init__(
        self,
        storage: BlobStoragePort,
        analyzer: AnalyzerPort,
        operation_storage: OperationStoragePort,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        self.storage = storage
        self.analyzer = analyzer
        self.operation_storage = operation_storage
        self.on_progress = on_progress or (lambda message: None)

    def run(
        self,
        limit: int = 2,
        execute: bool = False,
    ) -> BatchSummary:
        if limit < 1:
            raise ValueError('Limit must be greater than zero.')

        container = self.storage.container_processed

        if not container:
            raise ValueError('Processed container is not configured.')

        operations = self.operation_storage.load()
        pdfs = self.storage.list_pdfs()

        pending = []
        skipped = 0

        for pdf_name in pdfs:
            json_name = str(PurePosixPath(pdf_name).with_suffix('.json'))

            if self.storage.blob_exists(container, json_name):
                skipped += 1

                if execute and pdf_name in operations:
                    del operations[pdf_name]
                    self.operation_storage.save(operations)

                continue

            pending.append((pdf_name, json_name))

        pending.sort(
            key=lambda item: (
                item[0] not in operations,
                item[0],
            )
        )

        selected = pending[:limit]

        summary = BatchSummary(
            total_pdfs=len(pdfs),
            already_processed=skipped,
            pending=len(pending),
            selected=len(selected),
            recoverable=sum(pdf_name in operations for pdf_name, _ in selected),
        )

        if not execute:
            return summary

        for index, (pdf_name, json_name) in enumerate(selected, start=1):
            self.on_progress(f'Processando documento {index}/{len(selected)}...')

            try:
                operation = operations.get(pdf_name)

                if operation is not None:
                    if operation.get('analyzer_id') != self.analyzer.analyzer_id:
                        raise ValueError('Operation belongs to another analyzer.')

                    operation_url = operation['operation_url']
                    self.on_progress('Recuperando análise anterior...')

                else:
                    pdf_bytes = self.storage.download_pdf(pdf_name)

                    operation_url = self.analyzer.start_analysis(pdf_bytes)

                    operations[pdf_name] = {
                        'operation_url': operation_url,
                        'analyzer_id': self.analyzer.analyzer_id,
                    }

                    self.operation_storage.save(operations)
                    self.on_progress('Nova análise registrada.')

                analysis = self.analyzer.get_analysis_result(operation_url)

                result = process_invoice(analysis)

                self.storage.upload_json(
                    container_name=container,
                    blob_name=json_name,
                    data=result,
                )

                del operations[pdf_name]
                self.operation_storage.save(operations)

                summary.processed += 1

                self.on_progress(f'Concluído: {result["reconciliation_status"]}')

            except TimeoutError:
                if pdf_name in operations:
                    summary.timed_out += 1
                    self.on_progress('Análise pendente. Operação preservada.')
                else:
                    summary.failed += 1
                    self.on_progress('Timeout antes do registro da operação.')

            except Exception as error:
                summary.failed += 1
                self.on_progress(f'Falha: {type(error).__name__}')

        return summary
