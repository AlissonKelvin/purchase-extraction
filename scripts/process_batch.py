import argparse
from pathlib import Path, PurePosixPath

from azure.core.exceptions import ResourceExistsError

from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)
from elis_procurement_v2.adapters.azure_content_understanding import (
    AzureContentUnderstanding,
)
from elis_procurement_v2.adapters.operation_storage import (
    OperationStorage,
)
from elis_procurement_v2.application.invoice_processor import (
    process_invoice,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=2)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()

    if args.limit < 1:
        parser.error('--limit must be greater than zero.')

    storage = AzureBlobStorage()
    analyzer = AzureContentUnderstanding()

    if not storage.container_processed:
        raise ValueError('Processed container is not configured.')

    operation_storage = OperationStorage(Path('data/private/pending_operations.json'))

    operations = operation_storage.load()
    pdfs = storage.list_pdfs()

    pending = []
    skipped = 0

    for pdf_name in pdfs:
        json_name = str(PurePosixPath(pdf_name).with_suffix('.json'))

        if storage.blob_exists(storage.container_processed, json_name):
            skipped += 1

            if pdf_name in operations:
                del operations[pdf_name]
                operation_storage.save(operations)

            continue

        pending.append((pdf_name, json_name))

    # Retoma primeiro operações já conhecidas.
    pending.sort(
        key=lambda item: (
            item[0] not in operations,
            item[0],
        )
    )

    selected = pending[: args.limit]

    print('--- Resumo do lote ---')
    print(f'PDFs encontrados: {len(pdfs)}')
    print(f'Já processados: {skipped}')
    print(f'Pendentes: {len(pending)}')
    print(f'Selecionados: {len(selected)}')
    print(
        'Operações recuperáveis selecionadas:',
        sum(pdf in operations for pdf, _ in selected),
    )

    if not args.execute:
        print('Modo simulação: nenhuma análise foi executada.')
        return

    processed = 0
    failed = 0
    timed_out = 0

    for index, (pdf_name, json_name) in enumerate(selected, start=1):
        print(f'Processando documento {index}/{len(selected)}...')

        try:
            operation = operations.get(pdf_name)

            if (
                operation is not None
                and operation.get('analyzer_id') == analyzer.analyzer_id
            ):
                operation_url = operation['operation_url']
                print('Recuperando análise anterior...')
            elif operation is not None:
                print(
                    'Operação de outro analisador encontrada. Revisão manual necessária.'
                )
                failed += 1
                continue
            else:
                pdf_bytes = storage.download_pdf(pdf_name)

                operation_url = analyzer.start_analysis(pdf_bytes)

                operations[pdf_name] = {
                    'operation_url': operation_url,
                    'analyzer_id': analyzer.analyzer_id,
                }
                operation_storage.save(operations)

                print('Nova análise iniciada e registrada.')

            analysis = analyzer.get_analysis_result(operation_url)
            result = process_invoice(analysis)

            storage.upload_json(
                container_name=storage.container_processed,
                blob_name=json_name,
                data=result,
            )

            del operations[pdf_name]
            operation_storage.save(operations)

            processed += 1
            print(f'Concluído: {result["reconciliation_status"]}')

        except TimeoutError:
            timed_out += 1
            print('Análise pendente. Operação preservada.')

        except ResourceExistsError:
            # Outro processo pode ter criado o resultado.
            # Não sobrescrevemos o arquivo existente.
            failed += 1
            print('O JSON de destino já existe.')

        except Exception as error:
            failed += 1
            print(f'Falha no processamento: {type(error).__name__}')

    print('--- Resultado final ---')
    print(f'Processados: {processed}')
    print(f'Ainda em análise: {timed_out}')
    print(f'Falhas: {failed}')
    print(f'Já existentes: {skipped}')


if __name__ == '__main__':
    main()
