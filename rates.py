import requests
from datetime import datetime

_FALLBACK = {"USD": 50.5, "SAR": 13.5, "EGP": 1.0}


def get_rates() -> dict:
    """
    Returns EGP value of 1 unit of each currency.
    {"USD": 50.5, "SAR": 13.5, "EGP": 1.0, "fetched_at": "...", "source": "live|fallback"}
    """
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=8)
        r.raise_for_status()
        data = r.json()
        raw = data["rates"]

        usd_to_egp = float(raw["EGP"])
        usd_to_sar = float(raw["SAR"])
        sar_to_egp = usd_to_egp / usd_to_sar

        return {
            "USD": round(usd_to_egp, 2),
            "SAR": round(sar_to_egp, 2),
            "EGP": 1.0,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "live",
        }
    except Exception:
        return {
            **_FALLBACK,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "fallback ⚠️",
        }


def to_egp(amount: float, currency: str, rates: dict) -> float:
    """Convert any amount to EGP using fetched rates."""
    rate = rates.get(currency.upper(), 1.0)
    return round(amount * rate, 2)
