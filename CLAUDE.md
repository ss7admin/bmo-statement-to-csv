# BMO Statement to CSV — Project Guide

## Project summary

This project is a Python CLI tool called `bmo2csv` that converts BMO bank statement PDFs into CSV files.

Primary goal:

- Parse BMO statement PDFs reliably.
- Output clean CSV rows with date, description, withdrawal, deposit, balance, statement date, and account number.
- Keep the parser easy to test and extend.

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
  test_parser.py     # 8 pytest tests (all passing)
```

## How the parser works (parser.py)

- `parse(pdf)` extracts raw text from all pages, then processes line by line
- `_parse_single_line()` checks if a line starts with a date token (e.g. "Apr02"), walks backwards from end to find trailing amounts
- `_classify()` decides debit vs credit based on description keywords
- `_merge_continuations()` merges merchant ID lines into the previous transaction
- Output: `List[Transaction]` objects

## Parser behavior

Important parser assumptions:

- Parsing is line-based after extracting text from all PDF pages.
- A transaction line usually begins with a compact date token such as `Apr02`.
- Amounts are detected by scanning from the end of the line backward.
- Debit/credit classification currently depends partly on description keywords.
- Continuation lines may belong to the previous transaction and should be merged carefully.

When changing parsing logic:

- Prefer small, targeted changes.
- Preserve existing passing behavior unless a test is intentionally updated.
- Add or update tests for every parsing edge case fixed.

## Coding guidance

- Keep the code simple and explicit.
- Prefer focused helper functions over large complex rewrites.
- Do not introduce heavy new dependencies unless clearly justified.
- Keep standard-library-first wherever possible.
- Preserve CLI compatibility unless explicitly changing the interface.

## Workflow

For non-trivial changes:

1. Read relevant files first.
2. Explain the plan before editing multiple files.
3. Make the smallest safe change.
4. Run tests after code changes.
5. Summarize what changed and any remaining risks.

Git workflow:

- Use the configured git identity for this repo. This repo uses machine user qzemcoder <claude@qzem.com>
- Do not add Claude attribution or co-author lines to commit messages.
- Prefer feature branches for larger changes.

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

8 tests, all passing.

## CLI usage

```bash
pip install -e .
bmo2csv "statement.pdf" output.csv
```

### Bulk conversion

Convert all PDFs in a directory:

```bash
bmo2csv --bulk <input_dir> [output_dir]
```

Output dir defaults to input_dir. Files that fail exit non-zero with error details.

## Notes for future sessions

Before making parser changes, inspect examples in tests and preserve output consistency.
If you fix a parsing bug, add a regression test whenever possible.

## Session expectations

1. **Read** relevant files before suggesting changes
2. **Test** after every code edit (`pytest`)
3. **Explain** reasoning for parser changes
4. **Preserve** existing working behavior

---

_Last updated: 2026-04-28_
