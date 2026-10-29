import argparse
from pathlib import PurePosixPath

from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)
from elis_procurement_v2.adapters.azure_content_understanding import (
    AzureContentUnderstanding,
)
from elis_procurement_v2.application.invoice_processor import (
    process_invoice,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Process a single invoice from Azure Blob Storage.'
    )
    parser.add_argument(
        'blob_name',
        help='PDF blob name in invoices-raw',
    )

    args = parser.parse_args()
    blob_name = args.blob_name

    storage = AzureBlobStorage()
    analyzer = AzureContentUnderstanding()

    storage = AzureBlobStorage()

    processed_container = storage.container_processed

    if not processed_container:
        raise ValueError('Processed container is not configured.')

    processed_blob_name = str(PurePosixPath(blob_name).with_suffix('.json'))

    if storage.blob_exists(
        container_name=processed_container,
        blob_name=processed_blob_name,
    ):
        print('This invoice has already been processed. Analysis will be skipped.')
        return

    analyzer = AzureContentUnderstanding()

    print('1. Downloading PDF...')
    pdf_bytes = storage.download_pdf(blob_name)

    print('2. Analysing with Content Understanding...')
    analysis = analyzer.analyze_pdf(pdf_bytes)

    print('3. Processing invoice...')
    result = process_invoice(analysis)

    if processed_container is None:
        raise ValueError('Processed container is not configured.')

    storage.upload_json(
        container_name=processed_container,
        blob_name=processed_blob_name,
        data=result,
    )

    print('JSON uploaded to invoices-processed!')

    print('--- Result ---')
    print(f'Line items: {result["line_items_count"]}')
    print(f'Charges: {result["charges_count"]}')
    print(f'Reconciliation: {result["reconciliation_status"]}')
    print(f'Review: {result["review_status"]}')


if __name__ == '__main__':
    main()
