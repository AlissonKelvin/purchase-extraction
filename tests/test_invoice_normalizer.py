from decimal import Decimal

from elis_procurement_v2.adapters.invoce_normalizer import normalize_invoice
from elis_procurement_v2.domain.models import Invoice, LineItem


def test_normalize_invoice():
    # Arrange
    data_raw = {
        'SupplierName': 'Global Industrial Ltd',
        'InvoiceNumber': 'INV-2026-001',
        'CurrencyCode': 'USD',
        'InvoiceTotal': '550.00',
        'LineItems': [
            {
                'Description': 'Industrial Pump',
                'Quantity': '2',
                'UnitPrice': '250.00',
            },
        ],
        'Charges': [
            {
                'Description': 'Freight',
                'Amount': '50.00',
            },
        ],
    }

    # Act
    invoice = normalize_invoice(data_raw)

    # Assert
    assert isinstance(invoice, Invoice)
    assert invoice.supplier_name == 'Global Industrial Ltd'
    assert invoice.invoice_number == 'INV-2026-001'
    assert invoice.currency_code == 'USD'
    assert invoice.invoice_total == Decimal('550.00')


def test_invoice_with_discount() -> None:
    invoice = Invoice(
        invoice_total=Decimal('50.54'),
        line_items=(
            LineItem(
                description='Work trousers',
                quantity=Decimal('1'),
                unit_price=Decimal('91.90'),
                line_amount=Decimal('50.54'),
            ),
        ),
    )

    assert invoice.calculated_total == Decimal('50.54')
    assert invoice.reconciliation_status == 'matched'


def test_invoice_requires_review() -> None:
    invoice = Invoice(
        invoice_total=Decimal('14328.00'),
        line_items=(
            LineItem(
                description='Industrial Trousers',
                quantity=Decimal('2.4'),
                quantity_raw='2,400',
                unit_price=Decimal('5.97'),
                line_amount=Decimal('14328.00'),
            ),
        ),
    )

    assert invoice.reconciliation_status == 'matched'
    assert invoice.has_item_mismatches is True
    assert invoice.review_status == 'review_required'
