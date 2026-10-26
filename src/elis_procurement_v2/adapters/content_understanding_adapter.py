from collections.abc import Mapping
from typing import Any


def extract_value(field: Any) -> Any:
    if not isinstance(field, Mapping):
        return None

    field_type = field.get('type')

    if field_type == 'string':
        value = field.get('valueString')
        if value is None:
            value = field.get('stringValue')
        return value

    if field_type in ('number', 'integer'):
        value = field.get('valueNumber')
        if value is None:
            value = field.get('numberValue')
        return value

    if field_type == 'array':
        value_array = field.get('valueArray')

        if value_array is None:
            return None

        return [extract_value(item) for item in value_array]

    if field_type == 'object':
        value_object = field.get('valueObject')

        if value_object is None:
            return None

        return {key: extract_value(value) for key, value in value_object.items()}

    return None


def adapt_content_understanding(
    response: Mapping[str, Any],
) -> dict[str, Any]:
    contents = response.get('result', {}).get('contents', [])

    if not contents:
        raise ValueError('No contents found in the response.')

    fields = contents[0].get('fields', {})

    return {key: extract_value(value) for key, value in fields.items()}


def adapt_invoice_schema(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    adapted = dict(data)

    def monetary_amount(value: Any) -> Any:
        if isinstance(value, Mapping):
            return value.get('Amount')
        return value

    total_amount = data.get('TotalAmount')

    if adapted.get('SupplierName') is None:
        adapted['SupplierName'] = data.get('VendorName')

    if adapted.get('InvoiceNumber') is None:
        adapted['InvoiceNumber'] = data.get('InvoiceId')

    if adapted.get('InvoiceTotal') is None:
        adapted['InvoiceTotal'] = monetary_amount(total_amount)

    if adapted.get('CurrencyCode') is None:
        if isinstance(total_amount, Mapping):
            adapted['CurrencyCode'] = total_amount.get('CurrencyCode')

    line_items = []

    for item in data.get('LineItems') or []:
        line_amount = item.get('LineAmount')

        if line_amount is None:
            line_amount = item.get('TotalAmount')

        line_items.append(
            {
                'Description': item.get('Description'),
                'Quantity': item.get('Quantity'),
                'QuantityRaw': item.get('QuantityRaw'),
                'UnitPrice': monetary_amount(item.get('UnitPrice')),
                'LineAmount': monetary_amount(line_amount),
            }
        )

    adapted['LineItems'] = line_items

    return adapted
