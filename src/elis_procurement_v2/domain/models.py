from dataclasses import dataclass
from decimal import Decimal


@dataclass
class LineItem:
    description: str
    quantity: Decimal
    quantity_raw: str
    unit_price: Decimal
    line_amount: Decimal


@dataclass(frozen=True, slots=True)
class Charge:
    description: str
    amount: Decimal | None = None
    rate: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Invoice:
    supplier_name: str | None = None
    invoce_number: str | None = None
    currency_code: str | None = None
    invoice_total: Decimal | None = None
    line_items: tuple[LineItem, ...] = ()
    charges: tuple[Charge, ...] = ()

    @property
    def calculated_total(self) -> Decimal | None:
        if any(
            item.quantity is None or item.unit_price is None for item in self.line_items
        ):
            return None

        if any(charge.amount is None for charge in self.charges):
            return None

        items_total = sum(
            (item.quantity * item.unit_price for item in self.line_items),
            Decimal('0'),
        )

        charges_total = sum(
            (charge.amount for charge in self.charges if charge.amount is not None),
            Decimal('0'),
        )

        return items_total + charges_total

    @property
    def reconciliation_difference(self) -> Decimal | None:
        calculated = self.calculated_total

        if calculated is None or self.invoice_total is None:
            return None

        return self.invoice_total - calculated

    @property
    def reconciliation_status(self) -> str:
        difference = self.reconciliation_difference

        if difference is None:
            return 'inconclusive'

        if difference == Decimal('0'):
            return 'matched'

        return 'mismatched'
