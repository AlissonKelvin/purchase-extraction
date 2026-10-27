from unittest.mock import Mock, patch

from elis_procurement_v2.adapters.operation_storage import (
    OperationStorage,
)
from elis_procurement_v2.application.batch_processor import (
    BatchProcessor,
)


def test_batch_dry_run_does_not_analyze(tmp_path):
    storage = Mock()
    storage.container_processed = 'invoices-processed'
    storage.list_pdfs.return_value = [
        'invoice-a.pdf',
        'invoice-b.pdf',
    ]
    storage.blob_exists.side_effect = [True, False]

    analyzer = Mock()
    analyzer.analyzer_id = 'test-analyzer'

    operation_storage = OperationStorage(tmp_path / 'operations.json')

    processor = BatchProcessor(
        storage,
        analyzer,
        operation_storage,
    )

    summary = processor.run(limit=1, execute=False)

    assert summary.total_pdfs == 2
    assert summary.already_processed == 1
    assert summary.selected == 1

    analyzer.start_analysis.assert_not_called()
    storage.download_pdf.assert_not_called()
    storage.upload_json.assert_not_called()


@patch('elis_procurement_v2.application.batch_processor.process_invoice')
def test_batch_recovers_existing_operation(
    mock_process_invoice,
    tmp_path,
):
    storage = Mock()
    storage.container_processed = 'invoices-processed'
    storage.list_pdfs.return_value = ['invoice-a.pdf']
    storage.blob_exists.return_value = False

    analyzer = Mock()
    analyzer.analyzer_id = 'test-analyzer'
    analyzer.get_analysis_result.return_value = {
        'status': 'Succeeded',
        'result': {'contents': []},
    }

    operation_storage = OperationStorage(tmp_path / 'operations.json')

    operation_storage.save(
        {
            'invoice-a.pdf': {
                'operation_url': 'https://example.com/operation/123',
                'analyzer_id': 'test-analyzer',
            },
        }
    )

    mock_process_invoice.return_value = {
        'reconciliation_status': 'matched',
    }

    processor = BatchProcessor(
        storage,
        analyzer,
        operation_storage,
    )

    summary = processor.run(limit=1, execute=True)

    assert summary.processed == 1
    assert summary.failed == 0

    analyzer.start_analysis.assert_not_called()
    analyzer.get_analysis_result.assert_called_once_with(
        'https://example.com/operation/123'
    )

    storage.upload_json.assert_called_once()
    assert operation_storage.load() == {}
