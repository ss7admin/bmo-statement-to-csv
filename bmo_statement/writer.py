"""Write parsed statements to CSV."""

import csv
from typing import List

from bmo_statement.models import Transaction


def write_csv(transactions: List[Transaction], output_path: str) -> None:
    """Write parsed transactions to a CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Withdrawal", "Deposit", "Balance"])
        for t in transactions:
            writer.writerow([
                t.date,
                t.description,
                _format_amount(t.withdrawal),
                _format_amount(t.deposit),
                _format_amount(t.balance),
            ])


def _format_amount(val) -> str:
    """Format a Decimal amount for CSV, or empty string if None."""
    if val is None:
        return ""
    return str(val)
