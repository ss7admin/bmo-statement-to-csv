"""Tests for the BMO statement parser."""

import os
import csv

import pytest
import pdfplumber

STMT_PATH = os.path.join(os.path.dirname(__file__), "statement.pdf")


@pytest.fixture(scope="module")
def pdf():
    with pdfplumber.open(STMT_PATH) as pdf:
        yield pdf


import pytest
import pdfplumber
from bmo_statement.parser import parse as parse_pdf
from bmo_statement.writer import write_csv

STMT_PATH = os.path.join(os.path.dirname(__file__), "statement.pdf")


@pytest.fixture(scope="module")
def parsed_transactions():
    with pdfplumber.open(STMT_PATH) as pdf:
        return parse_pdf(pdf)


class TestParser:
    def test_returns_list(self, parsed_transactions):
        assert isinstance(parsed_transactions, list)

    def test_has_transactions(self, parsed_transactions):
        assert len(parsed_transactions) > 0

    def test_transaction_types(self, parsed_transactions):
        for t in parsed_transactions:
            assert hasattr(t, 'date')
            assert hasattr(t, 'description')
            assert hasattr(t, 'withdrawal')
            assert hasattr(t, 'deposit')
            assert hasattr(t, 'balance')

    def test_opening_balance(self, parsed_transactions):
        opening = [t for t in parsed_transactions if 'opening' in t.description.lower()]
        assert len(opening) > 0
        assert opening[0].balance is not None


class TestCSVWriter:
    def test_writes_csv(self, parsed_transactions, tmp_path):
        output = tmp_path / "test.csv"
        write_csv(parsed_transactions, str(output))
        assert output.exists()

    def test_csv_format(self, parsed_transactions, tmp_path):
        output = tmp_path / "test.csv"
        write_csv(parsed_transactions, str(output))
        with open(output) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["Date", "Description", "Withdrawal", "Deposit", "Balance"]

    def test_csv_content(self, parsed_transactions, tmp_path):
        output = tmp_path / "test.csv"
        write_csv(parsed_transactions, str(output))
        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(parsed_transactions)
            opening = [r for r in rows if 'opening' in r['Description'].lower()]
            assert len(opening) == 1
