# Procurement v2

Procurement v2 is a Python pipeline that extracts structured procurement
data from PDF invoices, reconciles invoice totals, and exports the results for
review and downstream analysis. It uses Azure Blob Storage for input and output
and Azure Content Understanding for document extraction.

The project currently runs as a set of command-line scripts. It supports both
single-invoice and resumable batch processing, produces structured JSON and CSV
files, and includes a local data-quality audit that does not make Azure calls.

## What the project does

1. Reads invoice PDFs from an Azure Blob Storage container.
2. Sends each PDF to a configured Azure Content Understanding analyser.
3. Adapts the analyser response to the project's invoice schema.
4. Normalises monetary and quantity values with `Decimal`.
5. Compares the extracted invoice total with the calculated total of line items
   and charges.
6. Stores one processed JSON file per invoice in Azure Blob Storage.
7. Exports validated processed data to semicolon-delimited CSV files.
8. Audits those CSV files for missing fields, amount mismatches, and suspicious
   quantity scaling.

## Processing flow

```text
Azure Blob Storage (PDF)
        |
        v
Azure Content Understanding
        |
        v
Schema adaptation and normalisation
        |
        v
Reconciliation and review flags
        |
        +--> Azure Blob Storage (processed JSON)
        |
        +--> Local CSV export --> Local quality audit
```

Batch operations that time out are saved locally and resumed on a later run.
This avoids submitting the same document again while Azure is still processing
it.

## Requirements

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- An Azure Storage account with raw and processed blob containers
- An Azure Content Understanding resource and invoice analyser

## Installation

Clone the repository and install the locked dependencies:

```bash
uv sync
```

Create a `.env` file in the repository root with the following settings:

```dotenv
AZURE_STORAGE_CONNECTION_STRING=<storage-connection-string>
AZURE_STORAGE_CONTAINER_RAW=invoices-raw
AZURE_STORAGE_CONTAINER_PROCESSED=invoices-processed
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://<resource>.cognitiveservices.azure.com
AZURE_CONTENT_UNDERSTANDING_KEY=<content-understanding-key>
AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID=<invoice-analyser-id>
```

The raw container must contain the source PDF files. The processed container is
used for JSON results. Blob paths are preserved: for example,
`2026/invoice-001.pdf` becomes `2026/invoice-001.json`.

Never commit `.env`, exported invoices, pending operation state, or other
customer data. These paths are excluded by `.gitignore`.

## Usage

### Process one invoice

Pass the PDF's blob name, including its virtual folder when applicable:

```bash
uv run python scripts/process_one_invoice.py "2026/invoice-001.pdf"
```

The command skips the Azure analysis when the corresponding processed JSON
already exists.

### Preview a batch

Batch processing is a dry run unless `--execute` is supplied:

```bash
uv run python scripts/process_batch.py --limit 10
```

The preview reports how many PDFs are pending, already processed, selected, or
associated with a recoverable Azure operation.

### Process a batch

```bash
uv run python scripts/process_batch.py --execute --limit 10
```

Pending Azure operation URLs are stored in
`data/private/pending_operations.json`. A later batch run resumes those
operations. The state file is removed entry by entry after successful uploads.

### Display the reconciliation report

```bash
uv run python scripts/report_processed.py
```

This aggregates all recognised processed JSON files by reconciliation status,
review status, and review reason. Non-invoice JSON files are counted as
unrecognised rather than included in the invoice totals.

### Export procurement data

```bash
uv run python scripts/export_procurement.py
```

The proof-of-concept export currently expects exactly 15 source PDFs and fails
before writing files if the source and processed data are incomplete or
inconsistent. It writes the following files to `data/private/delivery/`:

- `invoices.csv`: one row per invoice
- `line_items.csv`: one row per invoice line item
- `charges.csv`: one row per additional charge
- `manifest.json`: row counts and reconciliation totals

CSV files use a semicolon delimiter and UTF-8 with a byte-order mark for
spreadsheet compatibility. Text values that could be interpreted as spreadsheet
formulas are escaped during export.

### Audit the export

Run the local audit after exporting the CSV files:

```bash
uv run python scripts/audit_procurement_csv.py
```

The audit verifies row counts and source-invoice relationships, then produces:

- `invoices_for_review.csv`: all invoices with quality flags and manual-review
  status
- `item_quality_issues.csv`: line items that require attention
- `quality_summary.json`: aggregate issue counts

The audit never marks an invoice as manually approved. Even a matched invoice
with no detected flags remains `pending_manual_validation`.

## Reconciliation rules

The calculated invoice total is the sum of:

- each extracted line amount, or `quantity * unit_price` when the line amount is
  absent; and
- all extracted charge amounts.

The reconciliation status is:

- `matched` when the extracted and calculated totals are exactly equal;
- `mismatched` when both totals are available but differ; or
- `inconclusive` when the total cannot be calculated.

A line item is flagged when `quantity * unit_price` differs from its extracted
line amount by more than `0.01`. Review reasons are stored as stable codes:

- `invoice_total_mismatch`
- `item_amount_mismatch`
- `inconclusive_reconciliation`

The CSV audit also detects required values that are missing and quantities such
as `2,400` or `1.234` that may have been interpreted with the wrong scale.

These checks identify records for review; they do not replace validation against
the original invoice PDF.

## Project structure

```text
src/_procurement_v2/
|-- adapters/       Azure clients, response adapters, normalisation, and storage
|-- application/    Processing, batching, reporting, export, and audit use cases
`-- domain/         Invoice, line-item, charge, and reconciliation rules
scripts/            Command-line entry points
tests/              Unit tests for domain, application, and adapter behaviour
data/private/       Local operation state and generated exports (not committed)
```

## Development

The repository uses Ruff for formatting and linting, and pytest for tests and
coverage. Task aliases are provided through Taskipy:

```bash
uv run task format
uv run task check
uv run task test
```

You can run the underlying tools directly as well:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

The full test task writes an HTML coverage report to `htmlcov/`.
