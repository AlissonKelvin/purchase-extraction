from unittest.mock import Mock

from elis_procurement_v2.application.reconciliation_report import (
    build_reconciliation_report,
)


def test_build_reconciliation_report():
    storage = Mock()

    storage.list_processed_jsons.return_value = [
        'invoice-a.json',
        'invoice-b.json',
        'invoice-c.json',
    ]

    storage.download_processed_json.side_effect = [
        {
            'reconciliation_status': 'matched',
            'review_status': 'no_issues_detected',
        },
        {
            'reconciliation_status': 'mismatched',
            'review_status': 'review_required',
        },
        {
            'reconciliation_status': 'inconclusive',
            'review_status': 'review_required',
        },
    ]

    report = build_reconciliation_report(storage)

    assert report.total == 3
    assert report.matched == 1
    assert report.mismatched == 1
    assert report.inconclusive == 1
    assert report.review_required == 2


def test_report_ignores_analyzer_configuration():
    storage = Mock()

    storage.list_processed_jsons.return_value = [
        'example-invoice.json',
        'analyzer-config.json',
    ]

    storage.download_processed_json.side_effect = [
        {
            'reconciliation_status': 'matched',
            'review_status': 'no_issues_detected',
        },
        {
            'baseAnalyzerId': 'prebuilt-invoice',
            'fieldSchema': {'fields': {}},
            'templateId': 'example',
        },
    ]

    report = build_reconciliation_report(storage)

    assert report.total == 1
    assert report.matched == 1
    assert report.unrecognized == 1
    assert report.other == 0


def test_report_counts_review_reasons_from_old_and_new_jsons():
    storage = Mock()

    storage.list_processed_jsons.return_value = [
        'old-invoice.json',
        'new-invoice.json',
    ]

    storage.download_processed_json.side_effect = [
        {
            'reconciliation_status': 'matched',
            'review_status': 'review_required',
            'line_items': [
                {'has_quantity_mismatch': True},
            ],
        },
        {
            'reconciliation_status': 'mismatched',
            'review_status': 'review_required',
            'review_reasons': [
                'invoice_total_mismatch',
                'item_amount_mismatch',
            ],
        },
    ]

    report = build_reconciliation_report(storage)

    assert report.total == 2
    assert report.review_required == 2
    assert report.invoice_total_mismatch == 1
    assert report.item_amount_mismatch == 2
    assert report.inconclusive_reconciliation == 0
