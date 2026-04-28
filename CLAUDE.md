# BMO Statement to CSV — Project Guide

## What this project does
CLI tool (`bmo2csv`) that converts BMO bank statement PDFs into CSV format.

## Architecture
```
bmo_statement/
  __init__.py        # package root (empty)
  models.py          # Transaction, StatementInfo, ParsedStatement dataclasses
  parser.py          # PDF parser — line-based extraction via pdfplumber
  writer.py          # CSV output writer
  cli.py             # CLI entry point (bmo2csv)
setup.py             # pip installable, console script: bmo2csv
tests/
  test_parser.py     # 7 pytest tests (all passing)
```

## How the parser works (parser.py)
- `parse(pdf)` extracts raw text from all pages, then processes line by line
- `_parse_single_line()` checks if a line starts with a date token (e.g. "Apr02"), walks backwards from end to find trailing amounts
- `_classify()` decides debit vs credit based on description keywords
- `_merge_continuations()` merges merchant ID lines into the previous transaction
- Output: `List[Transaction]` objects

## Key data model (models.py)
```python
Transaction  # date, description, withdrawal, deposit, balance, statement_date, account_number
StatementInfo  # branch, transit, account, opening/closing balance, dates
ParsedStatement  # info, transactions, errors
```

## Dependencies
- pdfplumber (PDF text extraction)
- Standard library only (csv, decimal, argparse, dataclasses)

## Running tests
```bash
python3 -m pytest tests/ -v
```
7 tests, all passing.

## CLI usage
```bash
pip install -e .
bmo2csv "statement.pdf" output.csv
```

## Known issues / TODO
- **Date format**: Raw "Apr02" — need conversion to MM/DD/YYYY
- **Description cleanup**: "INTERACe-TransferReceived" should be "Interac e-Transfer Received"
- **Description cleanup**: "DebitCardPurchase,ONLINEPURCHASE" should be "Debit Card Purchase - ONLINE PURCHASE"
- **Amount formatting**: Should show as "666.66" not raw Decimal
- **Balance handling**: Some balances appear in separate columns, causing duplicates
- **Multi-page PDFs**: Only tested on single-page
- **Statement metadata**: `StatementInfo` fields not populated during parse
- **Error handling**: Basic, needs validation
