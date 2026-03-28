"""
tracker.py — Parse messages, log to Google Sheets, read summaries.
"""
import re
from datetime import datetime

from config import CATEGORIES, UNCATEGORIZED, SALARY, FIXED_MONTHLY
from rates import get_rates, to_egp
from sheets import ws, ensure_sheets

# ── Message Parsing ───────────────────────────────────────────────────────────

_PARSE = re.compile(
    r'^(.+?)\s+(\d+(?:[.,]\d+)?)\s*(usd|sar|egp)?\s*(.*)$',
    re.IGNORECASE,
)


def parse_message(text: str) -> dict | None:
    m = _PARSE.match(text.strip())
    if not m:
        return None

    description = m.group(1).strip()
    amount      = float(m.group(2).replace(",", "."))
    currency    = (m.group(3) or "EGP").upper()
    extra       = m.group(4).strip()

    combined = f"{description} {extra}".lower()

    return {
        "description": description.title(),
        "amount":      amount,
        "currency":    currency,
        "category":    _detect_category(combined),
        "source":      _detect_source(combined),
        "notes":       extra,
    }


def _detect_category(text: str) -> str:
    for cat, keywords in CATEGORIES.items():
        if any(k in text for k in keywords):
            return cat
    return UNCATEGORIZED


def _detect_source(text: str) -> str:
    mapping = {
        "swype":   "CIB Swype",
        "cib":     "CIB Platinum",
        "hsbc":    "HSBC",
        "fawry":   "Fawry",
        "khazna":  "Khazna",
        "premium": "Premium Card",
        "cash":    "Cash",
        "atm":     "Cash",
        "wallet":  "Phone Wallet",
    }
    for kw, source in mapping.items():
        if kw in text:
            return source
    return "-"


# ── Write ─────────────────────────────────────────────────────────────────────

def log_expense(parsed: dict) -> dict:
    rates      = get_rates()
    egp_amount = to_egp(parsed["amount"], parsed["currency"], rates)
    rate_used  = rates.get(parsed["currency"].upper(), 1.0)
    now        = datetime.now()

    # Transactions sheet
    ws("Transactions").append_row([
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M"),
        parsed["description"],
        parsed["amount"],
        parsed["currency"],
        rate_used,
        egp_amount,
        parsed["category"],
        parsed["source"],
        parsed.get("notes", ""),
    ])

    # Rates log
    ws("Rates Log").append_row([
        rates["fetched_at"],
        rates["USD"],
        rates["SAR"],
        rates["source"],
    ])

    return {**parsed, "egp_amount": egp_amount, "rate": rate_used, "rates": rates}


def undo_last() -> dict | None:
    w       = ws("Transactions")
    rows    = w.get_all_values()
    if len(rows) <= 1:
        return None

    last_idx = len(rows)          # 1-based row index
    last     = rows[last_idx - 1]
    data = {
        "description": last[2] if len(last) > 2 else "?",
        "egp_amount":  float(last[6]) if len(last) > 6 and last[6] else 0,
        "category":    last[7] if len(last) > 7 else "?",
    }
    w.delete_rows(last_idx)
    return data


# ── Read Summaries ────────────────────────────────────────────────────────────

def get_month_summary(month: str | None = None) -> dict:
    month = month or datetime.now().strftime("%Y-%m")

    rows    = ws("Transactions").get_all_values()
    by_cat  = {}
    total   = 0.0
    count   = 0

    for row in rows[1:]:                        # skip header
        if not row or not row[0].startswith(month):
            continue
        try:
            amt = float(row[6])
        except (ValueError, IndexError):
            continue
        cat = row[7] if len(row) > 7 else UNCATEGORIZED
        by_cat[cat] = by_cat.get(cat, 0.0) + amt
        total  += amt
        count  += 1

    fixed     = sum(FIXED_MONTHLY.values())
    remaining = SALARY - fixed - total

    return {
        "month":       month,
        "total":       round(total, 2),
        "count":       count,
        "by_category": by_cat,
        "fixed":       round(fixed, 2),
        "salary":      SALARY,
        "remaining":   round(remaining, 2),
    }
