"""Data models for parsed BMO statement transactions."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass
class Transaction:
    """A single transaction from a BMO bank statement."""
    date: str
    description: str
    withdrawal: Optional[Decimal] = None
    deposit: Optional[Decimal] = None
    balance: Optional[Decimal] = None
    statement_date: str = ""
    account_number: str = ""

    @property
    def net_change(self) -> Optional[Decimal]:
        """Net change to account (positive = deposit, negative = withdrawal)."""
        if self.deposit is None and self.withdrawal is None:
            return None
        deposit = self.deposit or Decimal("0")
        withdrawal = self.withdrawal or Decimal("0")
        return deposit - withdrawal


@dataclass
class StatementInfo:
    """Metadata about the parsed statement."""
    branch_name: str = ""
    transit_number: str = ""
    account_number: str = ""
    account_name: str = ""
    account_type: str = ""
    opening_balance: Decimal = Decimal("0.00")
    closing_balance: Decimal = Decimal("0.00")
    opening_date: Optional[date] = None
    closing_date: Optional[date] = None
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None


@dataclass
class ParsedStatement:
    """Complete parsed statement with transactions and metadata."""
    info: StatementInfo = field(default_factory=StatementInfo)
    transactions: list[Transaction] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ParsingError(Exception):
    """Error during statement parsing."""
