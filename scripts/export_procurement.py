from pathlib import Path

from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)
from elis_procurement_v2.application.procurement_exporter import (
    export_procurement_data,
)


def main() -> None:
    summary = export_procurement_data(
        storage=AzureBlobStorage(),
        output_dir=Path('data/private/delivery'),
        expected_pdfs=15,
    )

    print('--- Proof-of-concept export ---')
    print(f'Invoices: {summary["invoices"]}')
    print(f'Line items: {summary["line_items"]}')
    print(f'Charges: {summary["charges"]}')
    print(f'Matched: {summary["matched"]}')
    print(f'Mismatched: {summary["mismatched"]}')
    print(f'Inconclusive: {summary["inconclusive"]}')
    print('Files generated in data/private/delivery/')


if __name__ == '__main__':
    main()
