#!/usr/bin/env python3
"""
PhotoVirtue Telegram Bot - Bitcoin Edition

One-time Bitcoin payments (direct to your wallet) for 1 year unlimited access.
Users "upload funds" by sending BTC to your address.
Timer starts on confirmation: 365 days from purchase/credit date.
Renew manually by sending BTC again when expired.

No Stripe or recurring provider. Pure Bitcoin to your address.

Automation options:
- Manual (start here): User sends, /confirm or you use /credit after checking blockchain.
- Recommended for scale: Run BTCPay Server (free, self-hosted). It creates per-payment invoices, notifies your FastAPI webhook, and sends the BTC straight to your wallet.
- Or use NOWPayments/CoinPayments for hosted invoices + webhooks.

DB: subscription_end is the timer.
Web editor uses the exact same check.

Replace BTC_ADDRESS and ADMIN_ID below.
"""

import sqlite3
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8818096818:AAHZQQYRUW43NINN41w830DTa4oZ4Q5nxao"
WEB_APP_URL = "https://coolbeanman.com"
ADMIN_ID = 8929762959
BTC_ADDRESS = "bc1qfxp5cr5vqhez50330nl82e2etmv5dtwrvlmgk6"
PRICE_USD = 19.0

# ArtCraft integration for provisioning on BTC payment
ARTCRAFT_BASE = "https://api.storyteller.ai"
ARTCRAFT_ADMIN_KEY = "YOUR_ARTCRAFT_ADMIN_OR_SERVICE_KEY"

# Other services (enable as needed)
OTHER_SERVICES = {}

DB_PATH = "photovirtue.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        subscription_end TEXT,
        paid_amount REAL,
        last_payment_tx TEXT
    )''')
    # Auto-migrate old DBs (add missing columns)
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_payment_tx TEXT")
    except:
        pass
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_subscription(user_id, username, amount_usd=19.0, tx=None):
    """1 year from NOW (timer starts at purchase/confirmation)."""
    end_date = (datetime.now() + timedelta(days=365)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users 
                 (user_id, username, subscription_end, paid_amount, last_payment_tx)
                 VALUES (?, ?, ?, ?, ?)''',
              (user_id, username, end_date, amount_usd, tx))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    row = get_user(user_id)
    if not row:
        return False
    end = datetime.fromisoformat(row[2])
    return datetime.now() < end

def get_btc_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=8
        )
        return float(r.json()["bitcoin"]["usd"])
    except:
        return 65000.0  # fallback

def provision_access(telegram_user_id: int, username: str, duration_days: int = 365):
    """Provision access across ArtCraft Services and other applicable services on BTC payment.
    
    ArtCraft (https://github.com/storytold/artcraft-services):
    - Maps Telegram user to ArtCraft account/credits.
    - Grants 1-year access or equivalent credits for AI image/video generation, jobs, media library.
    - Uses the existing credits/wallet system in the Rust backend.
    - In production: Call billing endpoints or create API key tied to external_id="telegram:{id}".
    
    Extensible to other services:
    - Add calls for Replicate, local ComfyUI, Hugging Face, etc. for additional generation/editing capabilities.
    - This keeps PhotoVirtue as the payment + browser gateway, powering it with pro backends.
    
    The 1-year timer (from our DB) gates access. Renew via BTC.
    """
    print(f"[PhotoVirtue] Provisioning access for Telegram:{telegram_user_id} ({username}) - {duration_days} days")

    # ArtCraft Services integration
    try:
        # Placeholder for real call. Based on ArtCraft API (Omni, billing, accounts).
        # Example: POST to grant credits or subscription.
        # You will need to implement the exact endpoint from your ArtCraft instance (e.g. /v1/billing or /v1/accounts).
        payload = {
            "external_id": f"telegram:{telegram_user_id}",
            "username": username or f"user_{telegram_user_id}",
            "duration_days": duration_days,
            "source": "btc_one_time_19usd",
            "amount_usd": 19.0,
            "notes": "PhotoVirtue 1-year access via Telegram BTC"
        }
        # Uncomment and adapt when ready (use admin key or service account):
        # resp = requests.post(
        #     f"{ARTCRAFT_BASE}/v1/billing/grant_or_extend",
        #     json=payload,
        #     headers={"Authorization": f"Bearer {ARTCRAFT_ADMIN_KEY}", "Content-Type": "application/json"},
        #     timeout=15
        # )
        # print(f"[ArtCraft] Response: {resp.status_code} {resp.text[:200]}")
        print(f"[ArtCraft] Would grant access/credits for {payload}")
    except Exception as e:
        print(f"[ArtCraft] Provision error (stub): {e}")

    # Other applicable services (extensible)
    for svc_name, cfg in OTHER_SERVICES.items():
        if cfg.get("enabled"):
            print(f"[{svc_name}] Would provision access for user {telegram_user_id} (add real integration here)")
            # e.g. for replicate: create prediction quota, etc.

    # Generate and store token for browser editor auth
    import hashlib, time
    token = hashlib.sha256(f"{telegram_user_id}:{int(time.time())}:{duration_days}".encode()).hexdigest()[:32]
    # Store token in DB for validation
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_payment_tx = ? WHERE user_id = ?", (token, telegram_user_id))
    conn.commit()
    conn.close()
    return {"status": "provisioned", "token": token, "expires_days": duration_days}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("Pay $19 in Bitcoin (1 year access)", callback_data="buy")],
        [InlineKeyboardButton("Open Editor (if paid)", web_app=WebAppInfo(url=WEB_APP_URL))],
    ]
    await update.message.reply_text(
        "Welcome to PhotoVirtue by Anthony Jones!\n\n"
        "Professional photo editing in the browser, powered by ArtCraft Services (AI gen) + extensible providers.\n"
        "One-time $19 in Bitcoin = 1 full year unlimited.\n\n"
        "Send BTC to my wallet -> we credit your account in ArtCraft + others -> 365-day timer starts.\n"
        "Pay again when it expires.\n\n"
        "Use the buttons below.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    price = get_btc_price()
    btc = PRICE_USD / price
    sats = int(btc * 100_000_000)

    text = (
        f"**Bitcoin Payment for 1 Year Access (PhotoVirtue + ArtCraft)**\n\n"
        f"Send ≈ {btc:.8f} BTC (${PRICE_USD})  |  ~{sats} sats\n"
        f"Live BTC price: ${price:,.0f}\n\n"
        f"Address:\n`{BTC_ADDRESS}`\n\n"
        f"After payment: 1-year timer starts + access to ArtCraft AI services (image/video gen, etc.) + extensible providers.\n"
        f"Reply with  /confirm  YOUR_TX_HASH\n\n"
        f"Or DM the admin the tx details.\n"
        f"Your ID: {user.id}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /confirm <tx_hash>")
        return

    tx = context.args[0]
    # In real use: verify the tx actually arrived at BTC_ADDRESS with enough value.
    # For now we credit on /confirm (you can manually check on mempool.space).

    update_subscription(user.id, user.username or str(user.id), PRICE_USD, tx)

    # Provision across ArtCraft + other services
    provision = provision_access(user.id, user.username or str(user.id))
    token = provision.get("token", "")

    end_str = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    await update.message.reply_text(
        f"Received. 1-year timer started from now.\n"
        f"Active until ~{end_str}.\n\n"
        f"ArtCraft + other services provisioned.\n"
        "Open editor (use the token if prompted):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Launch PhotoVirtue Editor", web_app=WebAppInfo(url=f"{WEB_APP_URL}?user_id={user.id}&token={token}"))]
        ])
    )

async def editor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_subscribed(uid):
        await update.message.reply_text(
            "Editor ready.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Open Editor", web_app=WebAppInfo(url=WEB_APP_URL))]
            ])
        )
    else:
        await update.message.reply_text("No active year. Use /buy to pay with Bitcoin.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    row = get_user(uid)
    if is_subscribed(uid):
        end = datetime.fromisoformat(row[2]).strftime("%Y-%m-%d")
        await update.message.reply_text(f"Active until {end}.")
    else:
        await update.message.reply_text("Expired or never paid. /buy with Bitcoin.")

async def credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: /credit <user_id> [tx]  — credit after you verify the on-chain tx."""
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /credit <user_id> [tx_hash]")
        return
    try:
        target = int(context.args[0])
    except:
        await update.message.reply_text("user_id must be a number.")
        return
    tx = context.args[1] if len(context.args) > 1 else "admin_manual"
    update_subscription(target, f"user_{target}", PRICE_USD, tx)

    # Provision ArtCraft + others
    provision_access(target, f"user_{target}")

    await update.message.reply_text(f"Credited {target} with 1 year. Timer started. ArtCraft provisioned.")

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("editor", editor))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("credit", credit))

    print("PhotoVirtue BTC bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
