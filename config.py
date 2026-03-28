import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot & Cloud ───────────────────────────────────────────────────────────────
BOT_TOKEN               = os.environ.get("BOT_TOKEN", "")
SPREADSHEET_ID          = os.environ.get("SPREADSHEET_ID", "")
# Local dev: path to JSON file. Cloud (Railway): raw JSON string as env var.
CREDENTIALS_FILE        = os.environ.get("CREDENTIALS_FILE", "")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")

# ── Income & Fixed Obligations ────────────────────────────────────────────────
SALARY = 51_700.0

FIXED_MONTHLY = {
    "Loan (until Nov 2029)": 8_272.44,
}

FAWRY_INSTALLMENTS = [11_483.84, 11_483.84, 4_139.00]

# ── Debt Snapshot (March 2026) ────────────────────────────────────────────────
DEBTS = [
    {"name": "CIB Platinum",  "type": "Credit Card", "limit": 50_000,  "available": 1_039.94},
    {"name": "CIB Swype",     "type": "Credit Card", "limit": 100_000, "available": 12_770.37},
    {"name": "HSBC",          "type": "Credit Card", "limit": 19_000,  "available": 0.00},
    {"name": "Fawry",         "type": "Fintech",     "limit": 51_000,  "available": 26_024.19},
    {"name": "Khazna",        "type": "Fintech",     "limit": 30_000,  "available": 30_000.00},
    {"name": "Premium Card",  "type": "Fintech",     "limit": 22_500,  "available": 22_500.00},
]

# ── Category Keywords ─────────────────────────────────────────────────────────
INCOME_KEYWORDS = ["salary", "income", "bonus", "freelance", "payment received"]

CATEGORIES = {
    "Food & Drink": [
        "coffee", "lunch", "dinner", "breakfast", "food", "pizza", "burger",
        "kfc", "mcdonalds", "restaurant", "cafe", "meal", "snack", "juice",
        "shawarma", "sushi", "delivery", "talabat", "eat", "drink", "water",
    ],
    "Transport": [
        "uber", "careem", "taxi", "metro", "bus", "petrol", "gas", "fuel",
        "parking", "toll", "train", "ride", "transport",
    ],
    "Shopping": [
        "clothes", "shirt", "shoes", "mall", "amazon", "noon", "shop",
        "store", "buy", "purchase", "ikea",
    ],
    "Entertainment": [
        "netflix", "spotify", "cinema", "movie", "game", "youtube",
        "prime", "gaming", "subscription", "ps",
    ],
    "Health": [
        "pharmacy", "doctor", "medicine", "clinic", "hospital", "lab",
        "test", "drug", "vitamins", "health",
    ],
    "Obligations": [
        "fawry", "loan", "installment", "cib", "hsbc", "credit",
        "minimum", "khazna", "premium", "payment",
    ],
    "Utilities & Bills": [
        "electricity", "water bill", "internet", "phone", "mobile", "wifi",
        "orange", "etisalat", "vodafone", "bill",
    ],
    "Cash Withdrawal": [
        "withdrawal", "atm", "cashout", "cash out", "withdraw",
    ],
    "Transfer": [
        "transfer", "instapay", "send money", "wallet",
    ],
}

UNCATEGORIZED = "Other"
