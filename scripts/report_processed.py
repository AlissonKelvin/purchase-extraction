from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)
from elis_procurement_v2.application.reconciliation_report import (
    build_reconciliation_report,
)


def main() -> None:
    storage = AzureBlobStorage()
    report = build_reconciliation_report(storage)

    print('--- Relatório de Reconciliação ---')
    print(f'Total de JSONs: {report.total}')
    print(f'Matched: {report.matched}')
    print(f'Mismatched: {report.mismatched}')
    print(f'Inconclusive: {report.inconclusive}')
    print(f'Outros status: {report.other}')
    print(f'Revisão necessária: {report.review_required}')
    print(f'JSONs não reconhecidos: {report.unrecognized}')

    print('--- Motivos de revisão ---')
    print(
        'Diferença no total da fatura:',
        report.invoice_total_mismatch,
    )
    print(
        'Divergência matemática em itens:',
        report.item_amount_mismatch,
    )
    print(
        'Reconciliação inconclusiva:',
        report.inconclusive_reconciliation,
    )


if __name__ == '__main__':
    main()
