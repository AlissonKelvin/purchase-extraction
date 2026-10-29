import csv
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Protocol


class InvoiceStoragePort(Protocol):
    container_processed: str | None

    def list_pdfs(self) -> list[str]: ...

    def blob_exists(self, container_name: str, blob_name: str) -> bool: ...

    def download_processed_json(self, blob_name: str) -> dict[str, Any]: ...


def safe_text(value: Any) -> str:
    text = '' if value is None else str(value)

    # Protect text fields against spreadsheet formula injection.
    if text.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + text

    return text


def write_csv(
    path: Path,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            delimiter=';',
        )
        writer.writeheader()
        writer.writerows(rows)


def export_procurement_data(
    storage: InvoiceStoragePort,
    output_dir: Path,
    expected_pdfs: int = 15,
) -> dict[str, int]:
    container = storage.container_processed

    if not container:
        raise ValueError('Processed container is not configured.')

    pdfs = storage.list_pdfs()

    if len(pdfs) != expected_pdfs:
        raise ValueError(f'Expected {expected_pdfs} PDFs, found {len(pdfs)}.')

    invoices = []
    line_items = []
    charges = []
    statuses = Counter()

    for pdf_name in pdfs:
        json_name = str(PurePosixPath(pdf_name).with_suffix('.json'))

        if not storage.blob_exists(container, json_name):
            raise ValueError('Missing processed JSON for a PDF.')

        data = storage.download_processed_json(json_name)

        status = data.get('reconciliation_status')

        if status not in {'matched', 'mismatched', 'inconclusive'}:
            raise ValueError('Unrecognized reconciliation status.')

        if data.get('review_status') not in {'review_required', 'no_issues_detected'}:
            raise ValueError('Unrecognized review status.')

        items = data.get('line_items')
        invoice_charges = data.get('charges')

        if not isinstance(items, list):
            raise ValueError('Invalid line items.')

        if not isinstance(invoice_charges, list):
            raise ValueError('Invalid charges.')

        if data.get('line_items_count') != len(items):
            raise ValueError('Line item count mismatch.')

        if data.get('charges_count') != len(invoice_charges):
            raise ValueError('Charge count mismatch.')

        reasons = data.get('review_reasons')

        if reasons is None:
            reasons = []

            if status == 'mismatched':
                reasons.append('invoice_total_mismatch')
            elif status == 'inconclusive':
                reasons.append('inconclusive_reconciliation')

            if any(item.get('has_quantity_mismatch') is True for item in items):
                reasons.append('item_amount_mismatch')

        if not isinstance(reasons, list):
            raise ValueError('Invalid review reasons.')

        invoice_number = safe_text(data.get('invoice_number'))
        currency_code = safe_text(data.get('currency_code'))
        source_pdf = safe_text(pdf_name)

        invoices.append(
            {
                'source_pdf': source_pdf,
                'supplier_name': safe_text(data.get('supplier_name')),
                'invoice_number': invoice_number,
                'currency_code': currency_code,
                'invoice_total': data.get('invoice_total'),
                'calculated_total': data.get('calculated_total'),
                'reconciliation_difference': data.get('reconciliation_difference'),
                'reconciliation_status': status,
                'review_status': data['review_status'],
                'review_reasons': '|'.join(reasons),
                'line_items_count': len(items),
                'charges_count': len(invoice_charges),
            }
        )

        statuses[status] += 1

        for index, item in enumerate(items, start=1):
            line_items.append(
                {
                    'source_pdf': source_pdf,
                    'invoice_number': invoice_number,
                    'currency_code': currency_code,
                    'item_index': index,
                    'description': safe_text(item.get('description')),
                    'quantity_raw': safe_text(item.get('quantity_raw')),
                    'quantity': item.get('quantity'),
                    'unit_price': item.get('unit_price'),
                    'line_amount': item.get('line_amount'),
                    'has_quantity_mismatch': item.get('has_quantity_mismatch'),
                }
            )

        for index, charge in enumerate(invoice_charges, start=1):
            charges.append(
                {
                    'source_pdf': source_pdf,
                    'invoice_number': invoice_number,
                    'charge_index': index,
                    'description': safe_text(charge.get('description')),
                    'amount': charge.get('amount'),
                    'rate': charge.get('rate'),
                }
            )

    # Do not write any files until validation is complete.
    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        output_dir / 'invoices.csv',
        [
            'source_pdf',
            'supplier_name',
            'invoice_number',
            'currency_code',
            'invoice_total',
            'calculated_total',
            'reconciliation_difference',
            'reconciliation_status',
            'review_status',
            'review_reasons',
            'line_items_count',
            'charges_count',
        ],
        invoices,
    )

    write_csv(
        output_dir / 'line_items.csv',
        [
            'source_pdf',
            'invoice_number',
            'currency_code',
            'item_index',
            'description',
            'quantity_raw',
            'quantity',
            'unit_price',
            'line_amount',
            'has_quantity_mismatch',
        ],
        line_items,
    )

    write_csv(
        output_dir / 'charges.csv',
        [
            'source_pdf',
            'invoice_number',
            'charge_index',
            'description',
            'amount',
            'rate',
        ],
        charges,
    )

    summary = {
        'invoices': len(invoices),
        'line_items': len(line_items),
        'charges': len(charges),
        'matched': statuses['matched'],
        'mismatched': statuses['mismatched'],
        'inconclusive': statuses['inconclusive'],
    }

    (output_dir / 'manifest.json').write_text(
        json.dumps(summary, indent=2),
        encoding='utf-8',
    )

    return summary
