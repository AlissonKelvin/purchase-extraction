from dataclasses import dataclass
from typing import Any, Protocol


class ProcessedStoragePort(Protocol):
    def list_processed_jsons(self) -> list[str]: ...

    def download_processed_json(
        self,
        blob_name: str,
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class ReconciliationReport:
    total: int = 0
    matched: int = 0
    mismatched: int = 0
    inconclusive: int = 0
    other: int = 0
    review_required: int = 0
    unrecognized: int = 0

    # Novos indicadores
    invoice_total_mismatch: int = 0
    item_amount_mismatch: int = 0
    inconclusive_reconciliation: int = 0


def build_reconciliation_report(
    storage: ProcessedStoragePort,
) -> ReconciliationReport:
    report = ReconciliationReport()

    for blob_name in storage.list_processed_jsons():
        result = storage.download_processed_json(blob_name)

        if 'reconciliation_status' not in result or 'review_status' not in result:
            report.unrecognized += 1
            continue

        report.total += 1

        status = result.get('reconciliation_status')

        if status == 'matched':
            report.matched += 1
        elif status == 'mismatched':
            report.mismatched += 1
        elif status == 'inconclusive':
            report.inconclusive += 1
        else:
            report.other += 1

        if result.get('review_status') == 'review_required':
            report.review_required += 1

        reasons = result.get('review_reasons')

        if reasons is None:
            # Compatibilidade com JSONs antigos.
            reasons = []

            if status == 'mismatched':
                reasons.append('invoice_total_mismatch')
            elif status == 'inconclusive':
                reasons.append('inconclusive_reconciliation')

            if any(
                item.get('has_quantity_mismatch') is True
                for item in result.get('line_items') or []
            ):
                reasons.append('item_amount_mismatch')

        if 'invoice_total_mismatch' in reasons:
            report.invoice_total_mismatch += 1

        if 'item_amount_mismatch' in reasons:
            report.item_amount_mismatch += 1

        if 'inconclusive_reconciliation' in reasons:
            report.inconclusive_reconciliation += 1

    return report
