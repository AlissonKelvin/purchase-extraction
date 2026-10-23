from elis_procurement_v2.application.invoice_processor import (
    process_invoice,
)


def test_process_invoice() -> None:
    response = {
        'result': {
            'contents': [
                {
                    'fields': {
                        'SupplierName': {
                            'type': 'string',
                            'stringValue': 'Example Supplier Ltd',
                        },
                        'InvoiceTotal': {
                            'type': 'number',
                            'numberValue': 150,
                        },
                        'LineItems': {
                            'type': 'array',
                            'valueArray': [
                                {
                                    'type': 'object',
                                    'valueObject': {
                                        'Description': {
                                            'type': 'string',
                                            'stringValue': 'Industrial Valve',
                                        },
                                        'Quantity': {
                                            'type': 'number',
                                            'numberValue': 2,
                                        },
                                        'UnitPrice': {
                                            'type': 'number',
                                            'numberValue': 75,
                                        },
                                        'LineAmount': {
                                            'type': 'number',
                                            'numberValue': 150,
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ],
        },
    }

    result = process_invoice(response)

    assert result['supplier_name'] == 'Example Supplier Ltd'
    assert result['calculated_total'] == '150'
    assert result['reconciliation_status'] == 'matched'
    assert result['review_status'] == 'no_issues_detected'
    assert result['line_items_count'] == 1
    assert len(result['line_items']) == 1
    assert result['line_items'][0]['description'] == 'Industrial Valve'
    assert result['line_items'][0]['quantity'] == '2'
    assert result['charges'] == []
