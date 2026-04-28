# BMO Statement to CSV

Convert BMO Business Banking statement PDFs into structured CSV files.

## Features

- Parses BMO business banking statement PDFs
- Extracts transaction date, description, debit, credit, and running balance
- Outputs a clean CSV file compatible with Excel, Google Sheets, and accounting software
- Supports INTERAC e-Transfers, debit card purchases, and recurring payments
- Handles PDF parsing artifacts (merged text, camelCase descriptions, continuation lines)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Install via pip (development mode)

```bash
git clone https://github.com/ss7admin/bmo-statement-to-csv.git
cd bmo-bank-statement-to-csv
pip install -e .
```

This installs the `bmo-statement` package and its dependencies (`pdfplumber`, `camelcade`) in editable/development mode, so changes to the code are reflected immediately.

### Install dependencies manually

```bash
pip install pdfplumber camelcade
```

## Usage

### Command Line

The tool provides a CLI entry point called `bmo-statement`:

```bash
bmo-statement <input.pdf> <output.csv>
```

**Arguments:**

| Argument     | Description                                    |
| ------------ | ---------------------------------------------- |
| `input.pdf`  | Path to the BMO business banking statement PDF |
| `output.csv` | Path for the output CSV file                   |

**Example:**

```bash
bmo-statement statement.pdf output.csv
```

Upon successful completion, the tool prints the number of transactions extracted:

```
Successfully converted statement.pdf output.csv
25 transactions written
```

### Python API

```python
import pdfplumber
from bmo_statement.parser import parse
from bmo_statement.writer import write_csv

with pdfplumber.open("statement.pdf") as pdf:
    transactions = parse(pdf)

write_csv(transactions, "output.csv")
```

Each `Transaction` object has the following fields:

| Field            | Type              | Description                             |
| ---------------- | ----------------- | --------------------------------------- |
| `date`           | `str`             | Transaction date in `MM/DD/YYYY` format |
| `description`    | `str`             | Cleaned transaction description         |
| `withdrawal`     | `Decimal \| None` | Amount withdrawn (negative transaction) |
| `deposit`        | `Decimal \| None` | Amount deposited (positive transaction) |
| `balance`        | `Decimal \| None` | Running balance after the transaction   |
| `statement_date` | `str`             | Statement period ending date            |

### CSV Output Format

The generated CSV has the following columns:

| Column        | Description                   |
| ------------- | ----------------------------- |
| `Date`        | Transaction date (MM/DD/YYYY) |
| `Description` | Transaction description       |
| `Withdrawal`  | Amount withdrawn              |
| `Deposit`     | Amount deposited              |
| `Balance`     | Running balance               |

Opening and closing balance lines are included in the output for reference.

### Bulk Conversion

Convert all PDFs in a directory at once:

```bash
bmo-statement --bulk <input_dir> [output_dir]
```

| Argument       | Description                                          |
| -------------- | ---------------------------------------------------- |
| `input_dir`    | Directory containing PDF statements                  |
| `output_dir`   | Optional output directory (defaults to `input_dir`) |

**Example:**

```bash
bmo-statement --bulk ./statements ./statements_csv
```

Output:

```
[OK] january.pdf -> january.csv (33 transactions)
[OK] february.pdf -> february.csv (28 transactions)

Done: 2 converted, 0 failed
```

Files that fail to parse are reported with their error and the tool exits non-zero.

## Supported Transaction Types

- INTERAC e-Transfers (Sent/Received)
- Debit Card Purchases (Online and Point-of-Sale)
- Recurring Payments
- System transfers
- Opening/Closing balance lines

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding a New PDF

Drop a sample BMO statement PDF into the `tests/` directory and run:

```bash
bmo-statement tests/sample.pdf tests/output.csv
cat tests/output.csv
```

## License

MIT
