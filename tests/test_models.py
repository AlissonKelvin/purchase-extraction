from decimal import Decimal

from elis_procurement_v2.domain.models import Charge, Invoice, LineItem


def test_line_item_creation():
    # Arrange
    description = 'Test Item'
    quantity = Decimal('5.0')
    quantity_raw = '5'
    unit_price = Decimal('10.00')
    line_amount = Decimal('50.00')

    # Act
    line_item = LineItem(
        description=description,
        quantity=quantity,
        quantity_raw=quantity_raw,
        unit_price=unit_price,
        line_amount=line_amount,
    )

    # Assert
    assert line_item.description == description
    assert line_item.quantity == quantity
    assert line_item.quantity_raw == quantity_raw
    assert line_item.unit_price == unit_price
    assert line_item.line_amount == line_amount


def test_charge_creation():
    # Arrange
    description = 'Test Charge'
    amount = Decimal('15.00')
    rate = Decimal('0.15')

    # Act
    charge = Charge(
        description=description,
        amount=amount,
        rate=rate,
    )

    # Assert
    assert charge.description == description
    assert charge.amount == amount
    assert charge.rate == rate


def test_charge_creation_with_none_values():
    # Arrange
    description = 'Test Charge with None'
    amount = None
    rate = None

    # Act
    charge = Charge(
        description=description,
        amount=amount,
        rate=rate,
    )

    # Assert
    assert charge.description == description
    assert charge.amount is None
    assert charge.rate is None


def test_charge_zero_amount_and_rate():
    # Arrange
    description = 'Test Charge with Zero'
    amount = Decimal('0.00')
    rate = Decimal('0.00')

    # Act
    charge = Charge(
        description=description,
        amount=amount,
        rate=rate,
    )

    # Assert
    assert charge.description == description
    assert charge.amount == amount
    assert charge.rate == rate


def test_invoice_creation():
    # Arrange
    supplier_name = 'Test Supplier'
    invoice_number = 'INV-001'
    currency_code = 'USD'
    invoice_total = Decimal('100.00')
    line_items = (
        LineItem(
            description='Item 1',
            quantity=Decimal('2.0'),
            quantity_raw='2',
            unit_price=Decimal('20.00'),
            line_amount=Decimal('40.00'),
        ),
        LineItem(
            description='Item 2',
            quantity=Decimal('3.0'),
            quantity_raw='3',
            unit_price=Decimal('20.00'),
            line_amount=Decimal('60.00'),
        ),
    )
    charges = (
        Charge(
            description='Shipping',
            amount=Decimal('10.00'),
            rate=Decimal('0.10'),
        ),
    )

    # Act
    invoice = Invoice(
        supplier_name=supplier_name,
        invoce_number=invoice_number,
        currency_code=currency_code,
        invoice_total=invoice_total,
        line_items=line_items,
        charges=charges,
    )

    # Assert
    assert invoice.supplier_name == supplier_name
    assert invoice.invoce_number == invoice_number
    assert invoice.currency_code == currency_code
    assert invoice.invoice_total == invoice_total
    assert invoice.line_items == line_items
    assert invoice.charges == charges


def test_invoice_calculated_total() -> None:
    invoice = Invoice(
        invoice_total=Decimal('835.00'),
        line_items=(
            LineItem(
                description='Industrial Pump',
                quantity=Decimal('2'),
                quantity_raw='2',
                unit_price=Decimal('250.00'),
                line_amount=Decimal('500.00'),
            ),
        ),
        charges=(
            Charge(
                description='Freight',
                amount=Decimal('50.00'),
            ),
        ),
    )

    assert invoice.calculated_total == Decimal('550.00')


def test_invoice_reconciliation() -> None:
    invoice = Invoice(
        invoice_total=Decimal('850.00'),
        line_items=(
            LineItem(
                description='Industrial Pump',
                quantity=Decimal('2'),
                quantity_raw='2',
                unit_price=Decimal('250.00'),
                line_amount=Decimal('500.00'),
            ),
        ),
        charges=(
            Charge(
                description='Freight',
                amount=Decimal('50.00'),
            ),
        ),
    )

    assert invoice.calculated_total == Decimal('550.00')
    assert invoice.reconciliation_difference == Decimal('300.00')
    assert invoice.reconciliation_status == 'mismatched'
