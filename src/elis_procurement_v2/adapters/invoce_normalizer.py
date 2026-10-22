from decimal import Decimal
from typing import Any, Mapping

from elis_procurement_v2.domain.models import Charge, Invoice, LineItem


def to_decimal(value: str | int | float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def normalize_line_item(data: Mapping[str, Any]) -> LineItem:
    return LineItem(
        description=str(data.get('Description') or ''),
        quantity=to_decimal(data.get('Quantity')) or Decimal('0'),
        quantity_raw=str(data.get('QuantityRaw') or ''),
        unit_price=to_decimal(data.get('UnitPrice')) or Decimal('0'),
        line_amount=to_decimal(data.get('LineAmount')) or Decimal('0'),
    )


def normalize_charge(data: Mapping[str, Any]) -> Charge:
    return Charge(
        description=str(data.get('Description') or ''),
        amount=to_decimal(data.get('Amount')),
        rate=to_decimal(data.get('Rate')),
    )


def normalize_invoice(data: Mapping[str, Any]) -> Invoice:

    line_items = tuple(normalize_line_item(item) for item in data.get('LineItems', []))

    charges = tuple(normalize_charge(charge) for charge in data.get('Charges', []))

    return Invoice(
        supplier_name=data.get('SupplierName'),
        invoice_number=data.get('InvoiceNumber'),
        currency_code=data.get('CurrencyCode'),
        invoice_total=to_decimal(data.get('InvoiceTotal')),
        line_items=line_items,
        charges=charges,
    )
