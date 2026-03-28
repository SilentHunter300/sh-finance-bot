"""
server.py — Telegram webhook handler for Vercel.
Telegram sends POST requests here. No polling needed. Runs on free Vercel tier.
"""
import requests as req
from flask import Flask, request, jsonify

from config import BOT_TOKEN
from sheets import get_config, set_config, ensure_sheets
from tracker import parse_message, log_expense, undo_last, get_month_summary
from rates import get_rates

app = Flask(__name__)
TGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"


def reply(chat_id, text):
    try:
        req.post(f"{TGRAM}/sendMessage",
                 json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                 timeout=8)
    except Exception as e:
        print(f"Reply error: {e}")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return jsonify({"ok": True})

    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()
    if not text:
        return jsonify({"ok": True})

    allowed = get_config("chat_id")

    # /start — lock bot to this account
    if text.startswith("/start"):
        if allowed is None:
            set_config("chat_id", chat_id)
            ensure_sheets()
            reply(chat_id,
                "*Silent Hunter Finance — ONLINE*\n\n"
                "Running 24/7 in the cloud. PC can be off forever.\n\n"
                "*Log an expense:*\n"
                "`coffee 45`\n"
                "`lunch 120 usd`\n"
                "`uber 85`\n"
                "`fawry 11484`\n"
                "`withdrawal 500`\n\n"
                "/balance — this month\n"
                "/rates — live USD & SAR\n"
                "/undo — remove last entry\n"
                "/help — commands"
            )
        elif chat_id == allowed:
            reply(chat_id, "Already running. You're good.")
        else:
            reply(chat_id, "Unauthorized.")
        return jsonify({"ok": True})

    # All other interactions require auth
    if allowed is None or chat_id != allowed:
        return jsonify({"ok": True})

    if text.startswith("/help"):
        reply(chat_id,
            "*How to log:*\n"
            "`description amount [currency]`\n\n"
            "`coffee 45`\n"
            "`lunch 120 usd`\n"
            "`netflix 15 usd`\n"
            "`fawry 11484`\n"
            "`withdrawal 500`\n\n"
            "Currency defaults to EGP.\n\n"
            "/balance /rates /undo"
        )

    elif text.startswith("/balance"):
        s = get_month_summary()
        lines = [f"*{s['month']} — Overview*\n"]
        if s["by_category"]:
            for cat, amt in sorted(s["by_category"].items(), key=lambda x: -x[1]):
                lines.append(f"{cat}: *{amt:,.0f} EGP*")
        else:
            lines.append("_No expenses logged yet._")
        lines += [
            "",
            f"Salary: *{s['salary']:,.0f} EGP*",
            f"Fixed (loan): *-{s['fixed']:,.0f} EGP*",
            f"Spent: *-{s['total']:,.0f} EGP* ({s['count']} entries)",
            "",
            f"Est. remaining: *{s['remaining']:,.0f} EGP*",
        ]
        reply(chat_id, "\n".join(lines))

    elif text.startswith("/rates"):
        r = get_rates()
        reply(chat_id,
            f"*Live Rates*\n\n"
            f"1 USD = *{r['USD']}* EGP\n"
            f"1 SAR = *{r['SAR']:.4f}* EGP\n\n"
            f"{r['fetched_at']} ({r['source']})"
        )

    elif text.startswith("/undo"):
        removed = undo_last()
        if not removed:
            reply(chat_id, "Nothing to undo.")
        else:
            reply(chat_id,
                f"*Removed:*\n"
                f"{removed['description']} — {removed['egp_amount']:,.2f} EGP\n"
                f"_{removed['category']}_"
            )

    else:
        parsed = parse_message(text)
        if not parsed:
            reply(chat_id, "Couldn't read that.\n\nTry: `coffee 45` or `lunch 120 usd`")
            return jsonify({"ok": True})

        result = log_expense(parsed)

        if parsed["currency"] != "EGP":
            amount_line = (
                f"{parsed['amount']} {parsed['currency']} "
                f"= *{result['egp_amount']:,.2f} EGP* "
                f"(rate: {result['rate']})"
            )
        else:
            amount_line = f"*{result['egp_amount']:,.2f} EGP*"

        s = get_month_summary()
        reply(chat_id,
            f"*{parsed['description']}*\n"
            f"{amount_line}\n"
            f"{parsed['category']} | {parsed['source']}\n\n"
            f"Month: *{s['total']:,.0f} EGP* ({s['count']} entries)\n"
            f"Left: *{s['remaining']:,.0f} EGP*"
        )

    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
def health():
    return "Silent Hunter Finance — Running", 200
