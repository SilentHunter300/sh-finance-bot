"""
bot.py — Silent Hunter Finance Telegram Bot
Runs on Railway (cloud), 24/7, no PC needed.
"""
import logging

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)

from config import BOT_TOKEN
from sheets import ensure_sheets, get_config, set_config
from tracker import parse_message, log_expense, undo_last, get_month_summary
from rates import get_rates

logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

def _authorized(update: Update) -> bool:
    allowed = get_config("chat_id")
    return allowed is not None and str(update.effective_chat.id) == allowed


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    allowed = get_config("chat_id")

    if allowed is None:
        set_config("chat_id", chat_id)
        ensure_sheets()
        await update.message.reply_text(
            "*Silent Hunter Finance — ONLINE*\n\n"
            "Bot locked to your account. Running 24/7 in the cloud.\n\n"
            "*Log an expense:*\n"
            "`coffee 45`\n"
            "`lunch 120 usd`\n"
            "`uber 85`\n"
            "`fawry 11484`\n"
            "`withdrawal 500`\n\n"
            "*Commands:*\n"
            "/balance — this month\n"
            "/rates — live USD & SAR\n"
            "/undo — remove last entry\n"
            "/help — show this again\n\n"
            "Watching. Always.",
            parse_mode="Markdown",
        )
    elif chat_id == allowed:
        await update.message.reply_text("Already running. You're good.")
    else:
        await update.message.reply_text("Unauthorized.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return
    await update.message.reply_text(
        "*How to log:*\n"
        "`description amount [currency]`\n\n"
        "`coffee 45`\n"
        "`lunch 120 usd`\n"
        "`netflix 15 usd`\n"
        "`fawry 11484`\n"
        "`withdrawal 500`\n\n"
        "Currency defaults to EGP.\n\n"
        "/balance /rates /undo",
        parse_mode="Markdown",
    )


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    s     = get_month_summary()
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

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    r = get_rates()
    await update.message.reply_text(
        f"*Live Rates*\n\n"
        f"1 USD = *{r['USD']}* EGP\n"
        f"1 SAR = *{r['SAR']:.4f}* EGP\n\n"
        f"{r['fetched_at']} ({r['source']})",
        parse_mode="Markdown",
    )


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return

    removed = undo_last()
    if not removed:
        await update.message.reply_text("Nothing to undo.")
        return

    await update.message.reply_text(
        f"*Removed:*\n"
        f"{removed['description']} — {removed['egp_amount']:,.2f} EGP\n"
        f"_{removed['category']}_",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed = get_config("chat_id")

    if allowed is None:
        await update.message.reply_text("Send /start first.")
        return

    if not _authorized(update):
        return

    text   = update.message.text.strip()
    parsed = parse_message(text)

    if not parsed:
        await update.message.reply_text(
            "Couldn't read that.\n\nTry: `coffee 45` or `lunch 120 usd`",
            parse_mode="Markdown",
        )
        return

    result = log_expense(parsed)
    rates  = result["rates"]

    if parsed["currency"] != "EGP":
        amount_line = (
            f"{parsed['amount']} {parsed['currency']} "
            f"= *{result['egp_amount']:,.2f} EGP* "
            f"(rate: {result['rate']})"
        )
    else:
        amount_line = f"*{result['egp_amount']:,.2f} EGP*"

    s = get_month_summary()

    await update.message.reply_text(
        f"*{parsed['description']}*\n"
        f"{amount_line}\n"
        f"{parsed['category']} | {parsed['source']}\n\n"
        f"Month: *{s['total']:,.0f} EGP* ({s['count']} entries)\n"
        f"Left: *{s['remaining']:,.0f} EGP*",
        parse_mode="Markdown",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Silent Hunter Finance Bot — STARTING (cloud mode)")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("rates",   cmd_rates))
    app.add_handler(CommandHandler("undo",    cmd_undo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
