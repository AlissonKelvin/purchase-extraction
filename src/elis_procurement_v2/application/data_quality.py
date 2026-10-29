"""Audit exported proof-of-concept CSV files locally without calling Azure."""

import csv
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ISSUE_CODES = (
    'missing_description',
    'missing_quantity',
    'missing_unit_price',
    'missing_line_amount',
    'item_amount_mismatch',
    'ambiguous_quantity_scale',
)

# Possible thousands-grouping formats, such as 2,400 or 1.234.
GROUPED_QUANTITY = re.compile(r'[1-9]\d{0,2}(?:[,.]\d{3})+')
TOLERANCE = Decimal('0.01')


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file, delimiter=';')
        if not reader.fieldnames:
            raise ValueError(f'CSV has no header: {path.name}')
        return list(reader.fieldnames), list(reader)


def _decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation, ValueError:
        return None
    return number if number.is_finite() else None


def ambiguous_quantity_scale(item: dict[str, str]) -> bool:
    """Flag strong evidence of a scale error without changing quantities."""
    raw = (item.get('quantity_raw') or '').strip()
    if not GROUPED_QUANTITY.fullmatch(raw):
        return False

    parsed = _decimal(item.get('quantity'))
    price = _decimal(item.get('unit_price'))
    line_amount = _decimal(item.get('line_amount'))
    if parsed is None or price is None or line_amount is None or price == 0:
        return False

    as_thousands = Decimal(raw.replace(',', '').replace('.', ''))
    return (
        as_thousands != parsed
        and abs(as_thousands * price - line_amount) <= TOLERANCE
        and abs(parsed * price - line_amount) > TOLERANCE
    )


def _item_issues(item: dict[str, str]) -> list[str]:
    issues = []
    for field in ('description', 'quantity', 'unit_price', 'line_amount'):
        if not (item.get(field) or '').strip():
            issues.append(f'missing_{field}')

    if (item.get('has_quantity_mismatch') or '').strip().lower() == 'true':
        issues.append('item_amount_mismatch')

    if ambiguous_quantity_scale(item):
        issues.append('ambiguous_quantity_scale')

    return issues


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)


def audit_procurement_export(delivery_dir: Path) -> dict:
    """Validate an export and create quality reports without changing its files."""
    invoice_columns, invoices = _read_csv(delivery_dir / 'invoices.csv')
    _, items = _read_csv(delivery_dir / 'line_items.csv')
    _, charges = _read_csv(delivery_dir / 'charges.csv')
    manifest = json.loads((delivery_dir / 'manifest.json').read_text(encoding='utf-8'))

    if (len(invoices), len(items), len(charges)) != (
        manifest['invoices'],
        manifest['line_items'],
        manifest['charges'],
    ):
        raise ValueError('CSV row counts do not match manifest.json.')

    invoice_by_pdf = {row['source_pdf']: row for row in invoices}
    if len(invoice_by_pdf) != len(invoices):
        raise ValueError('Duplicate source_pdf value in invoices.csv.')

    item_counts = Counter(item['source_pdf'] for item in items)
    charge_counts = Counter(charge['source_pdf'] for charge in charges)
    if (set(item_counts) | set(charge_counts)) - set(invoice_by_pdf):
        raise ValueError('Line items or charges have no source invoice.')

    for pdf, invoice in invoice_by_pdf.items():
        if item_counts[pdf] != int(invoice['line_items_count']) or charge_counts[
            pdf
        ] != int(invoice['charges_count']):
            raise ValueError('Line item or charge count does not match the invoice.')

    issues_per_invoice = defaultdict(set)
    counts = Counter()
    item_issues = []
    for item in items:
        issues = _item_issues(item)
        if not issues:
            continue
        counts.update(issues)
        issues_per_invoice[item['source_pdf']].update(issues)
        item_issues.append(
            {
                'source_pdf': item['source_pdf'],
                'item_index': item['item_index'],
                'quantity_raw': item['quantity_raw'],
                'quantity': item['quantity'],
                'issue_codes': '|'.join(issues),
            }
        )

    invoice_reviews = []
    for invoice in invoices:
        flags = issues_per_invoice.get(invoice['source_pdf'], set())
        invoice_reviews.append(
            {
                **invoice,
                'quality_status': 'flags_detected' if flags else 'no_flags_detected',
                'quality_flags': '|'.join(code for code in ISSUE_CODES if code in flags),
                # Neither status proves that the source PDF was manually validated.
                'manual_validation_status': 'pending_manual_validation',
            }
        )

    summary = {
        'invoices': len(invoices),
        'line_items': len(items),
        'charges': len(charges),
        'flagged_invoices': len(issues_per_invoice),
        'flagged_items': len(item_issues),
        'issue_counts': {code: counts[code] for code in ISSUE_CODES},
        'manual_validation_status': 'pending_manual_validation',
    }

    _write_csv(
        delivery_dir / 'invoices_for_review.csv',
        invoice_columns
        + ['quality_status', 'quality_flags', 'manual_validation_status'],
        invoice_reviews,
    )
    _write_csv(
        delivery_dir / 'item_quality_issues.csv',
        ['source_pdf', 'item_index', 'quantity_raw', 'quantity', 'issue_codes'],
        item_issues,
    )
    (delivery_dir / 'quality_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    return summary
