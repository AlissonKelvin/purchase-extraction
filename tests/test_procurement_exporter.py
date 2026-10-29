import csv
import json
from unittest.mock import Mock

from elis_procurement_v2.application.procurement_exporter import (
    export_procurement_data,
)


def test_export_procurement_data(tmp_path):
    storage = Mock()
    storage.container_processed = 'invoices-processed'
    storage.list_pdfs.return_value = ['example.pdf']
    storage.blob_exists.return_value = True

    storage.download_processed_json.return_value = {
        'supplier_name': 'Example Supplier',
        'invoice_number': 'INV-001',
        'currency_code': 'EUR',
        'invoice_total': '20',
        'calculated_total': '20',
        'reconciliation_difference': '0',
        'reconciliation_status': 'matched',
        'review_status': 'no_issues_detected',
        'line_items_count': 1,
        'charges_count': 0,
        'line_items': [
            {
                'description': 'Example Product',
                'quantity_raw': '2',
                'quantity': '2',
                'unit_price': '10',
                'line_amount': '20',
                'has_quantity_mismatch': False,
            }
        ],
        'charges': [],
    }

    summary = export_procurement_data(storage, tmp_path, expected_pdfs=1)

    assert summary['invoices'] == 1
    assert summary['line_items'] == 1
    assert summary['charges'] == 0

    with (tmp_path / 'invoices.csv').open(encoding='utf-8-sig', newline='') as file:
        rows = list(csv.DictReader(file, delimiter=';'))

    assert len(rows) == 1
    assert rows[0]['invoice_number'] == 'INV-001'

    manifest = json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8'))

    assert manifest['matched'] == 1
