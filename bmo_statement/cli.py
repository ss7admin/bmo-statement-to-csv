"""CLI entry point for converting BMO statement PDFs to CSV."""

import argparse
import sys
import pdfplumber
from bmo_statement.parser import parse
from bmo_statement.writer import write_csv


def main():
    parser = argparse.ArgumentParser(description="Convert BMO bank statement PDFs to CSV")
    parser.add_argument("input", help="Path to the BMO statement PDF file")
    parser.add_argument("output", help="Path for the output CSV file")
    args = parser.parse_args()

    try:
        with pdfplumber.open(args.input) as pdf:
            transactions = parse(pdf)
        write_csv(transactions, args.output)
        print(f"Successfully converted {args.input} -> {args.output}")
        print(f"{len(transactions)} transactions written")
    except FileNotFoundError:
        print(f"Error: File '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
