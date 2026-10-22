import pytest

from elis_procurement_v2.adapters.content_understanding_adapter import (
    adapt_content_understanding,
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
