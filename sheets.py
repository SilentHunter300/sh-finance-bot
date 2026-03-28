"""
sheets.py — Google Sheets client and sheet management.
Single connection, reused across all calls.

Credentials priority:
  1. CREDENTIALS_FILE env var  → local JSON file (dev)
  2. GOOGLE_CREDENTIALS_JSON   → raw JSON string (Railway / cloud)
"""
import json
import gspread
from config import CREDENTIALS_FILE, GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID, DEBTS

# ── Singleton connection ──────────────────────────────────────────────────────
_ss = None


def spreadsheet():
    global _ss
    if _ss is None:
        if CREDENTIALS_FILE:
            client = gspread.service_account(filename=CREDENTIALS_FILE)
        elif GOOGLE_CREDENTIALS_JSON:
            client = gspread.service_account_from_dict(json.loads(GOOGLE_CREDENTIALS_JSON))
        else:
            raise RuntimeError("No Google credentials found. Set CREDENTIALS_FILE or GOOGLE_CREDENTIALS_JSON.")
        _ss = client.open_by_key(SPREADSHEET_ID)
    return _ss


def ws(name: str):
    return spreadsheet().worksheet(name)


# ── Sheet Bootstrap ───────────────────────────────────────────────────────────

SHEETS = {
    "Transactions": ["Date", "Time", "Description", "Amount", "Currency",
                     "Rate to EGP", "EGP Amount", "Category", "Source", "Notes"],
    "Debts":        ["Name", "Type", "Limit EGP", "Available EGP",
                     "Used EGP", "% Used", "Status"],
    "Rates Log":    ["Timestamp", "USD to EGP", "SAR to EGP", "Source"],
    "Config":       ["Key", "Value"],
}


def ensure_sheets():
    """Create missing sheets and populate initial data."""
    ss = spreadsheet()
    existing = {w.title for w in ss.worksheets()}

    for name, headers in SHEETS.items():
        if name not in existing:
            w = ss.add_worksheet(title=name, rows=2000, cols=max(len(headers) + 2, 10))
            w.append_row(headers)

    # Remove default empty sheet
    for default in ("Sheet1", "Sheet 1"):
        if default in existing:
            try:
                ss.del_worksheet(ss.worksheet(default))
            except Exception:
                pass

    # Populate Debts if empty
    debts_ws = ws("Debts")
    if len(debts_ws.get_all_values()) <= 1:
        for d in DEBTS:
            used = d["limit"] - d["available"]
            pct  = used / d["limit"] * 100
            if pct >= 99:
                status = "MAXED"
            elif pct >= 80:
                status = "HIGH"
            elif pct >= 50:
                status = "MEDIUM"
            else:
                status = "OK"
            debts_ws.append_row([
                d["name"], d["type"],
                d["limit"], d["available"],
                round(used, 2), f"{pct:.1f}%", status,
            ])


# ── Config store (chat_id etc.) ───────────────────────────────────────────────

def get_config(key: str) -> str | None:
    try:
        records = ws("Config").get_all_records()
        for r in records:
            if r.get("Key") == key:
                v = r.get("Value", "")
                return str(v) if v != "" else None
    except Exception:
        pass
    return None


def set_config(key: str, value: str):
    w = ws("Config")
    all_rows = w.get_all_values()
    for i, row in enumerate(all_rows):
        if row and row[0] == key:
            w.update_cell(i + 1, 2, value)
            return
    w.append_row([key, value])
