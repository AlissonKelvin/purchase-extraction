from pathlib import Path

from elis_procurement_v2.application.data_quality import audit_procurement_export


def main() -> None:
    directory = Path('data/private/delivery')
    summary = audit_procurement_export(directory)
    print('--- CSV audit ---')
    print(f'Invoices: {summary["invoices"]}')
    print(f'Line items: {summary["line_items"]}')
    print(f'Flagged invoices: {summary["flagged_invoices"]}')
    print(f'Flagged line items: {summary["flagged_items"]}')
    for reason, count in summary['issue_counts'].items():
        print(f'{reason}: {count}')
    print('Human review: pending for all invoices')
    print('Reports generated in data/private/delivery/')


if __name__ == '__main__':
    main()
