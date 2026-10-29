from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)
from elis_procurement_v2.application.reconciliation_report import (
    build_reconciliation_report,
)


def main() -> None:
    storage = AzureBlobStorage()
    report = build_reconciliation_report(storage)

    print('--- Reconciliation Report ---')
    print(f'Total JSON files: {report.total}')
    print(f'Matched: {report.matched}')
    print(f'Mismatched: {report.mismatched}')
    print(f'Inconclusive: {report.inconclusive}')
    print(f'Other statuses: {report.other}')
    print(f'Review required: {report.review_required}')
    print(f'Unrecognised JSON files: {report.unrecognized}')

    print('--- Review reasons ---')
    print(
        'Invoice total mismatch:',
        report.invoice_total_mismatch,
    )
    print(
        'Line item calculation mismatch:',
        report.item_amount_mismatch,
    )
    print(
        'Inconclusive reconciliation:',
        report.inconclusive_reconciliation,
    )


if __name__ == '__main__':
    main()
