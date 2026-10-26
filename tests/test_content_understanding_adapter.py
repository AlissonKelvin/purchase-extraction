import pytest

from elis_procurement_v2.adapters.content_understanding_adapter import (
    adapt_content_understanding,
    adapt_invoice_schema,
    extract_value,
)


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ({'type': 'string', 'stringValue': 'Invoice 123'}, 'Invoice 123'),
        ({'type': 'number', 'numberValue': 12.5}, 12.5),
        ({'type': 'integer', 'numberValue': 12}, 12),
        (
            {
                'type': 'array',
                'valueArray': [
                    {'type': 'string', 'stringValue': 'Item'},
                    {'type': 'number', 'numberValue': 2},
                ],
            },
            ['Item', 2],
        ),
        (
            {
                'type': 'object',
                'valueObject': {
                    'description': {'type': 'string', 'stringValue': 'Freight'},
                    'amount': {'type': 'number', 'numberValue': 25},
                },
            },
            {'description': 'Freight', 'amount': 25},
        ),
        ({'type': 'unsupported'}, None),
        ({'type': 'string'}, None),
        ({'type': 'array', 'valueArray': None}, None),
        ({'type': 'object', 'valueObject': None}, None),
        ('not a field mapping', None),
        (None, None),
    ],
)
def test_extract_value(field, expected):
    assert extract_value(field) == expected


def test_adapt_content_understanding_extracts_fields_from_first_content():
    response = {
        'result': {
            'contents': [
                {
                    'fields': {
                        'InvoiceNumber': {
                            'type': 'string',
                            'stringValue': 'INV-2026-001',
                        },
                        'InvoiceTotal': {'type': 'number', 'numberValue': 550.0},
                        'LineItems': {
                            'type': 'array',
                            'valueArray': [
                                {
                                    'type': 'object',
                                    'valueObject': {
                                        'description': {
                                            'type': 'string',
                                            'stringValue': 'Industrial Pump',
                                        },
                                        'quantity': {
                                            'type': 'integer',
                                            'numberValue': 2,
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
                {'fields': {'ignored': {'type': 'string', 'stringValue': 'later'}}},
            ],
        },
    }

    assert adapt_content_understanding(response) == {
        'InvoiceNumber': 'INV-2026-001',
        'InvoiceTotal': 550.0,
        'LineItems': [
            {'description': 'Industrial Pump', 'quantity': 2},
        ],
    }


@pytest.mark.parametrize(
    'response',
    [
        {},
        {'result': {}},
        {'result': {'contents': []}},
    ],
)
def test_adapt_content_understanding_raises_when_response_has_no_contents(response):
    with pytest.raises(ValueError, match='No contents found in the response\\.'):
        adapt_content_understanding(response)


def test_adapt_content_understanding_returns_empty_mapping_when_first_content_has_no_fields():
    assert adapt_content_understanding({'result': {'contents': [{}]}}) == {}


def test_adapt_invoice_schema_with_monetary_objects():
    data = {
        'LineItems': [
            {
                'Description': 'Example Product',
                'Quantity': 4,
                'UnitPrice': {
                    'Amount': 25.50,
                    'CurrencyCode': 'EUR',
                },
                'TotalAmount': {
                    'Amount': 100.00,
                    'CurrencyCode': 'EUR',
                },
            }
        ]
    }

    result = adapt_invoice_schema(data)
    item = result['LineItems'][0]

    assert item['Quantity'] == 4
    assert item['UnitPrice'] == 25.50
    assert item['LineAmount'] == 100.00


def test_adapt_invoice_schema_with_foundry_fields():
    data = {
        'VendorName': 'Example Supplier',
        'InvoiceId': 'INV-001',
        'TotalAmount': {
            'Amount': 150.00,
            'CurrencyCode': 'EUR',
        },
        'LineItems': [
            {
                'Description': 'Example Product',
                'Quantity': 3,
                'UnitPrice': {
                    'Amount': 50.00,
                    'CurrencyCode': 'EUR',
                },
                'TotalAmount': {
                    'Amount': 150.00,
                    'CurrencyCode': 'EUR',
                },
            },
        ],
    }

    result = adapt_invoice_schema(data)

    assert result['SupplierName'] == 'Example Supplier'
    assert result['InvoiceNumber'] == 'INV-001'
    assert result['InvoiceTotal'] == 150.00
    assert result['CurrencyCode'] == 'EUR'
    assert result['LineItems'][0]['UnitPrice'] == 50.00
    assert result['LineItems'][0]['LineAmount'] == 150.00
