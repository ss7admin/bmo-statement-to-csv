# BMO Statement to CSV

## Description preservation invariant

Transaction descriptions must preserve the raw text extracted from the PDF.

Allowed transformation:

- If a transaction description spans multiple lines, join those lines into a single description using one space.

Not allowed:

- Do not rewrite descriptions for readability.
- Do not normalize wording.
- Do not remove merchant IDs or trailing tokens.
- Do not discard text after embedded dates.
- Do not shorten descriptions to a cleaner phrase.

The description field must contain the full original text from the PDF, only flattened to one line.

## Project summary

This project is a Python CLI tool called `bmo2csv` that converts BMO bank statement PDFs into CSV files.

Primary goals:

- Parse BMO statement PDFs reliably.
- Output CSV rows with: `date, description, withdrawal, deposit, balance, statement_date, account_number`.
- Keep the parser easy to test and extend.

## Repository structure

```text
bmo_statement/
  __init__.py
  models.py      # Transaction, StatementInfo, ParsedStatement dataclasses
  parser.py      # PDF parser using pdfplumber
  writer.py      # CSV output writer
  cli.py         # CLI entry point (bmo2csv)

setup.py
pyproject.toml
tests/
  test_parser.py
```

## Key commands

Install locally:

```bash
pip install -e .
```

Run tests:

```bash
python3 -m pytest tests/ -v
```

Run CLI:

```bash
bmo2csv "statement.pdf" output.csv
```

Bulk mode:

```bash
bmo2csv --bulk <input_dir> [output_dir]
```

Output directory defaults to `input_dir`.

## Parser behavior

Important parser assumptions:

- Parsing is line-based after extracting text from all PDF pages.
- A transaction line usually begins with a compact date token such as `Apr02`.
- Amounts are detected by scanning from the end of the line backward.
- Debit/credit classification may use keywords.
- Continuation lines may belong to the previous transaction and should be merged carefully.

## Description handling rules

Transaction descriptions must preserve the raw text extracted from the PDF.

Hard rules:

- Do **not** rewrite, simplify, normalize, clean up, or improve transaction descriptions.
- Do **not** remove merchant, service, product, or location details from continuation lines.
- If a transaction description spans multiple lines, merge those lines into a single description field.
- When merging multi-line descriptions, preserve the original text content and join lines using a single space only.
- The final CSV description must contain the full original PDF description text on one line.

Example:

- If PDF lines are:
  - `Debit Card Purchase, ONLINE PURCHASE 3APR2025`
  - `AMZN MKTP CA F1 9PQ67G ON`
- Final description should be:
  - `Debit Card Purchase, ONLINE PURCHASE 3APR2025 AMZN MKTP CA F1 9PQ67G ON`

## Parser change rules

When changing parsing logic:

- Prefer small, targeted changes.
- Preserve existing passing behavior unless a test is intentionally updated.
- Add or update tests for every parsing edge case fixed.
- If fixing a parsing bug, add a regression test whenever possible.
- Before changing parser behavior, inspect current tests and preserve output consistency unless the change is intentional.

## Coding guidance

- Keep the code simple and explicit.
- Prefer focused helper functions over large rewrites.
- Do not introduce heavy new dependencies unless clearly justified.
- Prefer standard library where possible.
- Preserve CLI compatibility unless explicitly changing the interface.

## Workflow

For non-trivial changes:

1. Read relevant files first.
2. Explain the plan before editing multiple files.
3. Make the smallest safe change.
4. Run tests after code changes.
5. Summarize what changed and any remaining risks.

## Git workflow

- Use the configured git identity for this repo: `qzemcoder <claude@qzem.com>`
- Do **not** add Claude attribution or co-author lines to commit messages.
- Prefer feature branches for larger changes.

## Data model

```python
Transaction      # date, description, withdrawal, deposit, balance, statement_date, account_number
StatementInfo    # branch, transit, account, opening/closing balance, dates
ParsedStatement  # info, transactions, errors
```

## Dependencies

- `pdfplumber`
- Standard library only for core logic (`csv`, `decimal`, `argparse`, `dataclasses`, etc.)

## Current status

- 8 pytest tests passing.
- Bulk conversion exists.
- Output directory defaults to input directory in bulk mode.

## Session expectations

1. Read relevant files before suggesting changes.
2. Test after every code edit.
3. Explain reasoning for parser changes.
4. Preserve existing working behavior unless an intentional change is requested.
