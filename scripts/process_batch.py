import argparse
from pathlib import Path

from elis_procurement_v2.adapters.azure_blob_storage import (
    AzureBlobStorage,
)
from elis_procurement_v2.adapters.azure_content_understanding import (
    AzureContentUnderstanding,
)
from elis_procurement_v2.adapters.operation_storage import (
    OperationStorage,
)
from elis_procurement_v2.application.batch_processor import (
    BatchProcessor,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Process invoices from Azure Blob Storage.'
    )

    parser.add_argument('--limit', type=int, default=2)
    parser.add_argument('--execute', action='store_true')

    args = parser.parse_args()

    if args.limit < 1:
        parser.error('--limit must be greater than zero.')

    processor = BatchProcessor(
        storage=AzureBlobStorage(),
        analyzer=AzureContentUnderstanding(),
        operation_storage=OperationStorage(Path('data/private/pending_operations.json')),
        on_progress=print,
    )

    summary = processor.run(
        limit=args.limit,
        execute=args.execute,
    )

    print('--- Batch summary ---')
    print(f'PDFs found: {summary.total_pdfs}')
    print(f'Already processed: {summary.already_processed}')
    print(f'Pending: {summary.pending}')
    print(f'Selected: {summary.selected}')
    print(f'Recoverable operations: {summary.recoverable}')

    if not args.execute:
        print('Dry-run mode: no analysis was performed.')
        return

    print('--- Final result ---')
    print(f'Processed: {summary.processed}')
    print(f'Still being analysed: {summary.timed_out}')
    print(f'Failed: {summary.failed}')


if __name__ == '__main__':
    main()
