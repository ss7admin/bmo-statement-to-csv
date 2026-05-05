"""Parser for BMO business banking statement PDFs."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import List, Optional, Tuple

import pdfplumber
from bmo_statement.models import Transaction



def extract_raw_lines(pdf: pdfplumber.PDF) -> List[str]:
    """Extract all raw text lines from all pages."""
    all_lines = []
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            all_lines.extend(text.split('\n'))
    return all_lines


def extract_statement_date(raw_lines: List[str]) -> str:
    """Extract the statement date from page header text."""
    for line in raw_lines:
        if 'period ending' in line.lower():
            return line.replace('For the period ending ', '').strip()
    return ''


def _is_date_token(text: str) -> bool:
    """Check if a token looks like a transaction date (e.g. Apr01, May05, 16APR2025)."""
    if len(text) not in (5, 6, 9):
        return False
    if len(text) == 5:
        month = text[:3].lower()
        return (
            month in ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
            and text[3:].isdigit()
        )
    # 6-char variant like "Apr 01" with a space
    if text[3] == ' ':
        month = text[:3].lower()
        return (
            month in ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
            and text[4:].isdigit()
        )
    # 9-char variant like "16APR2025" (DDMMYYYY format)
    day = text[:2]
    month = text[2:5].lower()
    year = text[5:]
    return (
        day.isdigit() and month in ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
        and year.isdigit() and len(year) == 4
    )


def _is_amount(text: str) -> bool:
    """Check if a string looks like a dollar amount."""
    if not text or not (text[0].isdigit() or text[0] == '-'):
        return False
    cleaned = text.replace(',', '').replace('$', '')
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _parse_amount(text: str) -> Optional[Decimal]:
    """Parse a dollar amount string to Decimal, handling commas."""
    cleaned = text.strip().replace(',', '').replace('$', '')
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


_MONTH_NAMES = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}


def _normalize_date(date_str: str, year: str) -> str:
    """Convert raw PDF date (e.g. 'Apr02', '16APR2025') to MM/DD/YYYY format."""
    if _is_date_token(date_str):
        if len(date_str) == 5:
            month_abbr = date_str[:3].lower()
            day = date_str[3:]
        elif len(date_str) == 6:
            month_abbr = date_str[:3].lower()
            day = date_str[4:]
        else:
            # 9-char DDMMYYYY format
            month_abbr = date_str[2:5].lower()
            day = date_str[:2]
        month = _MONTH_NAMES.get(month_abbr)
        if month and day.isdigit():
            return f"{month}/{day.zfill(2)}/{year}"
    return date_str


def _extract_year(statement_date: str) -> str:
    """Extract the 4-digit year from a parsed statement date string."""
    for part in statement_date.split():
        if len(part) == 4 and part.isdigit():
            return part
    return str(2025)


def _strip_merchant_id(text: str) -> str:
    """Extract and return a BMO merchant ID if it's prepended to the text.

    Merchant IDs appear on the line before a Debit Card Purchase and look like:
        AMZNMKTPCAF19PQ67GON  (Alibaba)
        ALIBABA.COMBC         (Alibaba)
        VISA*XXXX             (Visa)
        MERCHAND            (generic)
    We return the merchant ID so it can be prepended to the cleaned description.
    """
    # Pattern 1: TRNID value (no dots, no spaces, not a simple amount)
    # These are pure alphanumeric merchant identifiers from the continuation line
    # Pattern 2: TRNID values can also be just the raw text before DebitCardPurchase
    # First check if there's a clear merchant ID from the continuation line
    # TRNIDs are typically 16+ chars, alphanumeric, no spaces
    if ' ' in text:
        first_word = text.split()[0]
        # Check if first word looks like a TRNID merchant ID
        # TRNIDs are typically all caps, alphanumeric, no lowercase
        if (all(c.isalnum() for c in first_word) and
            len(first_word) >= 8 and
            first_word.isupper()):
            return first_word
    return ''


def _clean_description(raw: str) -> str:
    """Clean up merged/compacted descriptions from PDF parsing."""
    # Handle INTERAC e-Transfer patterns
    if 'INTERAC' in raw and 'e-Transfer' in raw:
        label = raw.strip()
        if 'Received' in label:
            return 'Interac e-Transfer Received'
        if 'Sent' in label:
            return 'Interac e-Transfer Sent'
        # Fallback — split INTERAC from the rest
        cleaned = label.replace('INTERAC', 'Interac')
        cleaned = cleaned.replace('e-Transfer', ' e-Transfer').strip()
        return cleaned

    # Handle Debit Card Purchase patterns (camelCase from PDF merge, e.g. DebitCardPurchase…)
    if 'DebitCardPurchase' in raw:
        prefix_start = raw.index('DebitCardPurchase')
        raw = raw[prefix_start:]
        prefix = 'Debit Card Purchase'
        rest = raw[len('DebitCardPurchase'):]

        rest = rest.strip(',').strip()

        # Try to find embedded date (e.g. 3APR2025) — may be followed by
        # merchant ID text after continuation-line merge
        date_match = None
        if rest:
            date_match = re.search(r'(\d{1,2})([A-Z]{3})(\d{4})', rest)
            if date_match:
                day = date_match.group(1)
                month_abbr = date_match.group(2).lower()
                year = date_match.group(3)
                type_part = rest[:date_match.start()].strip(',').strip()
            else:
                type_part = rest.strip(',').strip()
        else:
            type_part = ''

        if type_part:
            type_part = _split_camel_case(type_part)

        if type_part:
            if date_match:
                month_num = _MONTH_NAMES.get(month_abbr, '')
                if month_num:
                    date_formatted = f"{month_num}/{day.zfill(2)}/{year}"
                else:
                    date_formatted = date_match.group(0)
                return f'{prefix} - {type_part} - {date_formatted}'
            return f'{prefix} - {type_part}'

        return prefix

    # Handle Debit Card Purchase patterns where the type is an all-caps merged
    # phrase (e.g. 'ONLINEPURCHASE 03APR2025' or 'ONLINEPURCHASE').
    # These come from PDF text extraction where "Debit Card Purchase" became
    # one token and the type description merged into it.
    if any(merged in raw for merged in _KNOWN_MERGED):
        # Find which known merged phrase is present
        matched_merged = None
        for merged, split_str in _KNOWN_MERGED.items():
            if merged in raw:
                matched_merged = merged
                break
        prefix = 'Debit Card Purchase'
        # Extract the part after the merged phrase
        idx = raw.index(matched_merged)
        after = raw[idx + len(matched_merged):].strip(',').strip()

        # Try to find embedded date — may be followed by merchant ID text
        # after continuation-line merge
        date_match = None
        if after:
            date_match = re.search(r'(\d{1,2})([A-Z]{3})(\d{4})', after)
            if date_match:
                day = date_match.group(1)
                month_abbr = date_match.group(2).lower()
                year = date_match.group(3)
                type_part = after[:date_match.start()].strip(',').strip()
            else:
                type_part = after
        else:
            type_part = ''

        if not type_part:
            # The entire after was just the date; the type is the matched phrase itself
            type_part = _split_camel_case(matched_merged)

        if type_part:
            type_part = _split_camel_case(type_part)

        if type_part:
            if date_match:
                month_num = _MONTH_NAMES.get(month_abbr, '')
                if month_num:
                    date_formatted = f"{month_num}/{day.zfill(2)}/{year}"
                else:
                    date_formatted = date_match.group(0)
                return f'{prefix} - {type_part} - {date_formatted}'
            return f'{prefix} - {type_part}'

    # Handle Opening/Closing statements (may be camelCase merged)
    if raw.startswith('Opening'):
        return 'Opening Balance'
    if raw.startswith('Closing') or 'Total' in raw:
        return 'Closing Total'

    # Handle PENDING patterns
    if 'PENDING' in raw and len(raw) > len('PENDING'):
        before_pending = raw[:raw.index('PENDING')].strip()
        after_pending = raw[raw.index('PENDING') + len('PENDING'):].strip()
        parts = []
        if before_pending:
            parts.append(before_pending)
        parts.append('PENDING')
        if after_pending:
            parts.append(after_pending)
        return ' '.join(parts)

    return raw


def _collapse_spaced_letters(text: str) -> str:
    """Collapse spaced-out letters like 'O N L I N E P U R C H A S E' into 'ONLINEPURCHASE'."""
    import re
    # Match sequences of single uppercase letters separated by spaces
    # Pattern: a single letter, then space-single-letter repeated
    pattern = r'(?<![a-zA-Z])([A-Z])(?:\s+[A-Z])+(?![a-zA-Z])'
    def replace_spaced(match):
        return re.sub(r'\s+', '', match.group(0))
    result = re.sub(pattern, replace_spaced, text)
    return result


# Known merged all-caps phrases from BMO PDF that regex can't split.
_KNOWN_MERGED = {
    'ONLINEPURCHASE': 'ONLINE PURCHASE',
    'RECURRINGPYMNT': 'RECURRING PYMNT',
    'RECURRINGPYPAYMT': 'RECURRING PYPAYMT',
}

def _split_camel_case(text: str) -> str:
    """Split camelCase or ALLCAPS merged text into readable words.

    Handles:
        'DebitCardPurchase' → 'Debit Card Purchase'
        'ONLINEPURCHASE' → 'ONLINE PURCHASE'
        'RECURRINGPYMNT' → 'RECURRING PYMNT'
        'Openingbalance' → 'Opening balance'
    """
    if not text:
        return ''
    # First collapse spaced letters: 'O N L I N E' -> 'ONLINE'
    text = _collapse_spaced_letters(text)
    # Try exact match lookup first
    if text in _KNOWN_MERGED:
        return _KNOWN_MERGED[text]
    # Try substring match for known merged phrases
    for merged, split_str in _KNOWN_MERGED.items():
        if merged in text:
            text = text.replace(merged, split_str)
            break
    # Insert spaces between consecutive uppercase letters where the second
    # letter starts a lowercase suffix.
    #     ONLINE|PURCHASE, Card|Purchase, Opening|balance
    text = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', text)
    # Join and collapse whitespace
    text = ' '.join(text.split())
    # Split any remaining camelCase boundaries not caught above
    result = []
    for i, char in enumerate(text):
        if i > 0 and char.isupper() and text[i-1].islower():
            result.append(' ')
        result.append(char)
    joined = ''.join(result)
    # Split trailing number: 'OnlinePurchase3' -> 'Online Purchase 3'
    joined = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', joined)
    return joined.strip()


def _parse_single_line(line: str) -> Optional[dict]:
    """Parse a single transaction line into a dict.

    Returns a dict with date, description_parts, amounts, and line_idx_hint.
    Or None if the line isn't a transaction line.
    """
    parts = line.split()
    if len(parts) < 2:
        return None

    date = parts[0]
    if not _is_date_token(date):
        return None

    # Walk backwards from end to find trailing amounts (balance/debit/credit)
    amounts = []
    idx = len(parts) - 1
    while idx > 0 and len(amounts) < 2:
        if _is_amount(parts[idx]):
            amounts.append(parts[idx])
            idx -= 1
        else:
            break

    description_parts = parts[1:idx + 1]
    if not description_parts:
        return None

    # Reconstruct raw description (before joining)
    raw_desc = ' '.join(description_parts)

    return {
        'date': date,
        'description_parts': description_parts,
        'amounts': list(reversed(amounts)),
        'raw_desc': raw_desc,
    }


def _classify(description: str, amounts: List[Decimal]) -> dict:
    """Classify the transaction type and set debit/credit/balance."""
    if len(amounts) < 2:
        if description.startswith('Opening'):
            return {'withdrawal': None, 'deposit': None, 'balance': amounts[0]}
        return {'withdrawal': amounts[0] if amounts else None, 'deposit': None, 'balance': None}

    if description.startswith('Closing') or 'Total' in description:
        return {'withdrawal': amounts[0], 'deposit': amounts[1], 'balance': None}

    if 'e-Transfer' in description or 'INTERAC' in description:
        return {'withdrawal': None, 'deposit': amounts[0], 'balance': amounts[1]}

    return {'withdrawal': amounts[0], 'deposit': None, 'balance': amounts[1]}


def _merge_continuations(parsed: List[dict], raw_lines: List[str]) -> List[dict]:
    """Merge continuation lines (merchant IDs on separate lines) into transactions."""
    result = []
    i = 0
    while i < len(parsed):
        entry = parsed[i]
        trn_id = ''

        # Check if there's a continuation line immediately after this transaction
        # Look ahead to see if the next line contains a TRNID
        next_line_idx = entry.get('_line_idx', i) + 1
        if next_line_idx < len(raw_lines):
            next_line = raw_lines[next_line_idx].strip()
            if next_line:
                # Check if the next line looks like a TRNID
                # TRNID lines typically start with TRNID: followed by alphanumeric ID
                trn_match = re.search(r'TRNID:(\S+)', next_line)
                if trn_match:
                    trn_id = trn_match.group(1)
                else:
                    # If it's not a TRNID line, check if it's a merchant ID
                    # Merchant IDs are typically all caps, alphanumeric, no spaces
                    if (next_line and all(c.isalnum() for c in next_line) and
                        len(next_line) >= 8 and next_line.isupper()):
                        trn_id = next_line

        entry['_line_idx'] = i
        entry['trn_id'] = trn_id
        result.append(entry)
        i += 1

    # Apply description cleaning to merged entries
    for entry in result:
        entry['raw_desc'] = _clean_description(entry['raw_desc'])

    return result


def _to_transaction(entry: dict, statement_date: str) -> Transaction:
    """Convert a parsed entry dict to a Transaction object."""
    year = _extract_year(statement_date)
    normalized_date = _normalize_date(entry['date'], year)

    # Use cleaned description (raw_desc already cleaned by _merge_continuations)
    raw = entry['raw_desc']
    if isinstance(raw, list):
        description = ' '.join(raw).strip()
    else:
        description = raw.strip()
    description = ' '.join(description.split())  # normalize whitespace

    classification = _classify(description, entry['amounts'])

    return Transaction(
        date=normalized_date,
        description=description,
        withdrawal=classification['withdrawal'],
        deposit=classification['deposit'],
        balance=classification['balance'],
        statement_date=statement_date,
        trn_id=entry.get('trn_id', ''),
    )


def parse(pdf: pdfplumber.PDF) -> List[Transaction]:
    """Parse a BMO statement PDF and return a list of Transaction objects."""
    raw_lines = extract_raw_lines(pdf)
    statement_date = extract_statement_date(raw_lines)

    # Parse each line
    parsed = []
    for line in raw_lines:
        result = _parse_single_line(line)
        if result:
            parsed.append(result)

    # Merge continuation lines into transactions
    parsed = _merge_continuations(parsed, raw_lines)

    # Convert to Transaction objects
    return [_to_transaction(e, statement_date) for e in parsed]