from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from elis_procurement_v2.adapters.content_understanding_adapter import (
    adapt_content_understanding,
)
from elis_procurement_v2.adapters.invoce_normalizer import normalize_invoice


def process_invoice(response: Mapping[str, Any]):
    data = adapt_content_understanding(response)
    invoice = normalize_invoice(data)

    return serialize_decimal(
        {
            'supplier_name': invoice.supplier_name,
            'invoice_number': invoice.invoice_number,
            'currency_code': invoice.currency_code,
            'invoice_total': invoice.invoice_total,
            'calculated_total': invoice.calculated_total,
            'reconciliation_difference': invoice.reconciliation_difference,
            'reconciliation_status': invoice.reconciliation_status,
            'review_status': invoice.review_status,
            'line_items_count': len(invoice.line_items),
            'charges_count': len(invoice.charges),
            'line_items': [
                {
                    'description': item.description,
                    'quantity': item.quantity,
                    'quantity_raw': item.quantity_raw,
                    'unit_price': item.unit_price,
                    'line_amount': item.line_amount,
                    'has_quantity_mismatch': item.has_quantity_mismatch,
                }
                for item in invoice.line_items
            ],
            'charges': [
                {
                    'description': charge.description,
                    'amount': charge.amount,
                    'rate': charge.rate,
                }
                for charge in invoice.charges
            ],
        }
    )


def serialize_decimal(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, dict):
        return {key: serialize_decimal(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [serialize_decimal(item) for item in value]

    return value
