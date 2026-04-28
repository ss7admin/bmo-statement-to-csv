---
name: bmo-statement-to-csv project
description: BMO bank statement PDF to CSV converter CLI — parser, writer, tests, known issues
type: project
---

# bmo-statement-to-csv Project Context

## What it does
CLI tool `bmo2csv` that converts BMO bank statement PDFs (PDFPlumber-extracted tables) into CSV with columns: Date, Description, Withdrawal, Deposit, Balance.

## Architecture
```
bmo_statement/
  __init__.py        # package root
  models.py          # Transaction, StatementInfo, ParsedStatement dataclasses
  parser.py          # PDF parser — line-based extraction via pdfplumber
  writer.py          # CSV output writer
  cli.py             # CLI entry point (bmo2csv)
setup.py             # pip installable, console script: bmo2csv
tests/
  test_parser.py     # 7 pytest tests (all passing)
```

## Key parser logic (parser.py)
- `parse(pdf)` → `List[Transaction]` — extracts raw text lines from all pages
- `_parse_single_line(line)` → checks if line starts with date token (3-letter month + digits like "Apr02"), then walks backwards from end to find amounts
- `_classify(desc, amounts)` → determines if it's transfer/debit/credit based on description keywords
- `_merge_continuations()` → merges merchant ID lines into previous transaction
- `_is_date_token()` validates "MonDD" or "Mon DD" format

## Date format
Currently outputs as "Apr02" (month abbreviation + day). Requested "MM/DD/YYYY" format but not yet implemented.

## Known issues / TODO
- **Date format**: Dates are raw "Apr02" — need conversion to MM/DD/YYYY
- **Description format**: Shows "INTERACe-TransferReceived" or "DebitCardPurchase,ONLINEPURCHASE" — needs cleanup to human-readable format
- **Amount formatting**: Raw Decimal values (e.g. "666.66") — should be formatted to 2 decimal places
- **Balance**: Some balances appear in separate columns, causing duplicates in CSV
- **Multi-page**: Only tested on single-page PDFs
- **Statement metadata**: `extract_statement_date()` works but `StatementInfo` fields not populated
- **Error handling**: Basic, should add more validation

## Running tests
```bash
python3 -m pytest tests/ -v
```
7 tests, all passing.

## Sample data
- `April 30, 2025.pdf` — single-page test PDF (33 transactions)
- `tests/statement.pdf` — copy for pytest fixture
