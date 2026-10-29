import csv
import json
from pathlib import Path

from elis_procurement_v2.application.data_quality import (
    ambiguous_quantity_scale,
    audit_procurement_export,
)


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)


def test_detects_suspected_thousands_separator():
    assert ambiguous_quantity_scale(
        {
            'quantity_raw': '2,400',
            'quantity': '2.4',
            'unit_price': '10',
            'line_amount': '24000',
        }
    )
    assert not ambiguous_quantity_scale(
        {
            'quantity_raw': '2,400',
            'quantity': '2.4',
            'unit_price': '10',
            'line_amount': '24',
        }
    )
    assert not ambiguous_quantity_scale(
        {
            'quantity_raw': '2,400',
            'quantity': '2400',
            'unit_price': '10',
            'line_amount': '24000',
        }
    )


def test_audits_export_without_approving_matched_invoice(tmp_path):
    write_csv(
        tmp_path / 'invoices.csv',
        [
            'source_pdf',
            'invoice_number',
            'reconciliation_status',
            'review_status',
            'line_items_count',
            'charges_count',
        ],
        [
            {
                'source_pdf': 'example.pdf',
                'invoice_number': 'INV-001',
                'reconciliation_status': 'matched',
                'review_status': 'no_issues_detected',
                'line_items_count': '2',
                'charges_count': '0',
            }
        ],
    )
    write_csv(
        tmp_path / 'line_items.csv',
        [
            'source_pdf',
            'item_index',
            'description',
            'quantity_raw',
            'quantity',
            'unit_price',
            'line_amount',
            'has_quantity_mismatch',
        ],
        [
            {
                'source_pdf': 'example.pdf',
                'item_index': '1',
                'description': 'Example product',
                'quantity_raw': '2,400',
                'quantity': '2.4',
                'unit_price': '10',
                'line_amount': '24000',
                'has_quantity_mismatch': 'True',
            },
            {
                'source_pdf': 'example.pdf',
                'item_index': '2',
                'description': '',
                'quantity_raw': '',
                'quantity': '',
                'unit_price': '',
                'line_amount': '',
                'has_quantity_mismatch': 'False',
            },
        ],
    )
    write_csv(tmp_path / 'charges.csv', ['source_pdf', 'charge_index'], [])
    (tmp_path / 'manifest.json').write_text(
        json.dumps({'invoices': 1, 'line_items': 2, 'charges': 0}), encoding='utf-8'
    )

    summary = audit_procurement_export(tmp_path)
    assert summary['flagged_invoices'] == 1
    assert summary['flagged_items'] == 2
    assert summary['issue_counts']['ambiguous_quantity_scale'] == 1
    assert summary['issue_counts']['missing_description'] == 1
    assert summary['issue_counts']['missing_quantity'] == 1

    with (tmp_path / 'invoices_for_review.csv').open(
        encoding='utf-8-sig', newline=''
    ) as file:
        invoice = next(csv.DictReader(file, delimiter=';'))
    assert invoice['reconciliation_status'] == 'matched'
    assert invoice['manual_validation_status'] == 'pending_manual_validation'
    assert invoice['quality_status'] == 'flags_detected'


def test_clean_invoice_remains_pending_manual_validation(tmp_path):
    write_csv(
        tmp_path / 'invoices.csv',
        [
            'source_pdf',
            'reconciliation_status',
            'review_status',
            'line_items_count',
            'charges_count',
        ],
        [
            {
                'source_pdf': 'clean.pdf',
                'reconciliation_status': 'matched',
                'review_status': 'no_issues_detected',
                'line_items_count': '1',
                'charges_count': '0',
            }
        ],
    )
    write_csv(
        tmp_path / 'line_items.csv',
        [
            'source_pdf',
            'item_index',
            'description',
            'quantity_raw',
            'quantity',
            'unit_price',
            'line_amount',
            'has_quantity_mismatch',
        ],
        [
            {
                'source_pdf': 'clean.pdf',
                'item_index': '1',
                'description': 'Good product',
                'quantity_raw': '2',
                'quantity': '2',
                'unit_price': '10',
                'line_amount': '20',
                'has_quantity_mismatch': 'False',
            }
        ],
    )
    write_csv(tmp_path / 'charges.csv', ['source_pdf', 'charge_index'], [])
    (tmp_path / 'manifest.json').write_text(
        json.dumps({'invoices': 1, 'line_items': 1, 'charges': 0}), encoding='utf-8'
    )

    summary = audit_procurement_export(tmp_path)
    assert summary['flagged_invoices'] == 0
    assert summary['flagged_items'] == 0
    with (tmp_path / 'invoices_for_review.csv').open(
        encoding='utf-8-sig', newline=''
    ) as file:
        invoice = next(csv.DictReader(file, delimiter=';'))
    assert invoice['quality_status'] == 'no_flags_detected'
    assert invoice['manual_validation_status'] == 'pending_manual_validation'
