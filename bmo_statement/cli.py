"""CLI entry point for converting BMO statement PDFs to CSV."""

import argparse
import os
import sys
from pathlib import Path
import pdfplumber
from bmo_statement.parser import parse
from bmo_statement.writer import write_csv


def convert_file(input_path, output_path):
    """Parse a single PDF and write CSV."""
    with pdfplumber.open(input_path) as pdf:
        transactions = parse(pdf)
    write_csv(transactions, output_path)
    return len(transactions)


def main():
    parser = argparse.ArgumentParser(
        description="Convert BMO bank statement PDFs to CSV"
    )
    parser.add_argument(
        "input",
        help="Path to the BMO statement PDF file or directory (use with --bulk)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Path for the output CSV file (required unless --bulk is used)",
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Convert all PDFs in the input directory to CSVs in the output directory",
    )
    args = parser.parse_args()

    if args.bulk:
        _bulk_convert(args)
    else:
        _single_convert(args)


def _single_convert(args):
    if not args.output:
        print("Error: --output is required when not using --bulk", file=sys.stderr)
        sys.exit(1)

    try:
        count = convert_file(args.input, args.output)
        print(f"Successfully converted {args.input} -> {args.output}")
        print(f"{count} transactions written")
    except FileNotFoundError:
        print(f"Error: File '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing PDF: {e}", file=sys.stderr)
        sys.exit(1)


def _bulk_convert(args):
    input_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else input_dir

    if not input_dir.is_dir():
        print(f"Error: '{args.input}' is not a directory", file=sys.stderr)
        sys.exit(1)

    pdfs = sorted(set(input_dir.glob("*.pdf")) | set(input_dir.glob("*.PDF")), key=lambda p: p.name)
    if not pdfs:
        print(f"No PDF files found in '{input_dir}'")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    success = 0
    failed = []

    for pdf_path in pdfs:
        csv_path = output_dir / (pdf_path.stem + ".csv")
        try:
            count = convert_file(str(pdf_path), str(csv_path))
            print(f"[OK] {pdf_path.name} -> {csv_path.name} ({count} transactions)")
            success += 1
        except Exception as e:
            print(f"[ERR] {pdf_path.name}: {e}")
            failed.append((pdf_path.name, e))

    print(f"\nDone: {success} converted, {len(failed)} failed")
    if failed:
        for name, e in failed:
            print(f"  {name}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
