from dataclasses import dataclass
from decimal import Decimal


@dataclass
class LineItem:
    description: str = ''
    quantity: Decimal | None = None
    quantity_raw: str = ''
    unit_price: Decimal | None = None
    line_amount: Decimal | None = None

    @property
    def has_quantity_mismatch(self) -> bool:
        if self.quantity is None or self.unit_price is None or self.line_amount is None:
            return False

        expected_amount = self.quantity * self.unit_price

        return abs(expected_amount - self.line_amount) > Decimal('0.01')


@dataclass(frozen=True, slots=True)
class Charge:
    description: str = ''
    amount: Decimal | None = None
    rate: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Invoice:
    supplier_name: str | None = None
    invoice_number: str | None = None
    currency_code: str | None = None
    invoice_total: Decimal | None = None
    line_items: tuple[LineItem, ...] = ()
    charges: tuple[Charge, ...] = ()

    @property
    def calculated_total(self) -> Decimal | None:
        if not self.line_items:
            return None

        items_total = Decimal('0')

        for item in self.line_items:
            if item.line_amount is not None:
                items_total += item.line_amount

            elif item.quantity is not None and item.unit_price is not None:
                items_total += item.quantity * item.unit_price

            else:
                return None

        charges_total = Decimal('0')

        for charge in self.charges:
            if charge.amount is None:
                return None

            charges_total += charge.amount

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

    @property
    def has_item_mismatches(self) -> bool:
        return any(item.has_quantity_mismatch for item in self.line_items)

    @property
    def review_status(self) -> str:
        if self.has_item_mismatches:
            return 'review_required'

        if self.reconciliation_status != 'matched':
            return 'review_required'

        return 'no_issued_detected'
