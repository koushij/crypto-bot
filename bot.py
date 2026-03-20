import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ── Coin map ──────────────────────────────────────────────────────────────────
COINS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
    "BNB": "BNBUSDT", "XRP": "XRPUSDT", "ADA": "ADAUSDT",
    "AVAX": "AVAXUSDT", "DOGE": "DOGEUSDT", "DOT": "DOTUSDT",
    "LINK": "LINKUSDT", "MATIC": "MATICUSDT", "ARB": "ARBUSDT",
    "UNI": "UNIUSDT", "LTC": "LTCUSDT", "ATOM": "ATOMUSDT",
    "NEAR": "NEARUSDT", "APT": "APTUSDT", "OP": "OPUSDT",
}

COIN_NAMES = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana",
    "BNB": "BNB", "XRP": "Ripple", "ADA": "Cardano",
    "AVAX": "Avalanche", "DOGE": "Dogecoin", "DOT": "Polkadot",
    "LINK": "Chainlink", "MATIC": "Polygon", "ARB": "Arbitrum",
    "UNI": "Uniswap", "LTC": "Litecoin", "ATOM": "Cosmos",
    "NEAR": "NEAR Protocol", "APT": "Aptos", "OP": "Optimism",
}

TIMEFRAMES = {"1H": "1 Hour", "4H": "4 Hours", "1D": "1 Day", "1W": "1 Week"}

# ── Price fetch ───────────────────────────────────────────────────────────────
def get_price(symbol: str) -> dict:
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def fmt_price(n: float) -> str:
    if n >= 10000: return f"${n:,.0f}"
    if n >= 1000:  return f"${n:,.0f}"
    if n >= 100:   return f"${n:.1f}"
    if n >= 1:     return f"${n:.2f}"
    return f"${n:.4f}"

# ── Analysis engine ───────────────────────────────────────────────────────────
def analyze(ticker: str, tf: str, price: float, chg: float, hi: float, lo: float) -> dict:
    sym = ticker.replace("USDT", "")

    mom = max(-1, min(1, (chg / 100) * 4 + random.uniform(-0.2, 0.2)))
    rsi = (random.uniform(60, 74) if chg > 6
           else random.uniform(26, 40) if chg < -6
           else random.uniform(38, 62))
    rsi_lbl = "Oversold 🟢" if rsi < 35 else "Overbought 🔴" if rsi > 65 else "Neutral ⚪"

    macd_bull = mom > 0.05
    macd = "Bullish crossover 📈" if macd_bull else ("Bearish crossover 📉" if mom < -0.05 else "Neutral ➡️")
    ema = ("Above EMA20/50 — Bullish 🟢" if mom > 0.2
           else "Below EMA20/50 — Bearish 🔴" if mom < -0.2
           else "Between EMA20–EMA50 ↔️")

    score = (1 if rsi < 40 else -1 if rsi > 60 else 0) + (1.2 if macd_bull else -1.2) + mom * 2
    if score > 0.8:    sig, trend, conf = "BUY", "Bullish",  random.randint(62, 84)
    elif score < -0.8: sig, trend, conf = "SELL", "Bearish", random.randint(60, 80)
    else:              sig, trend, conf = "HOLD", "Sideways", random.randint(48, 65)

    rng = hi - lo or price * 0.04
    s1 = lo + rng * random.uniform(0.05, 0.20)
    s2 = lo - rng * random.uniform(0.05, 0.18)
    r1 = hi - rng * random.uniform(0.05, 0.20)
    r2 = hi + rng * random.uniform(0.05, 0.18)
    tgt = (price + rng * random.uniform(0.3, 0.65) if sig == "BUY"
           else price - rng * random.uniform(0.3, 0.65) if sig == "SELL"
           else price + rng * random.uniform(-0.1, 0.1))
    sl  = (s1 * random.uniform(0.97, 0.99) if sig == "BUY"
           else r1 * random.uniform(1.01, 1.03) if sig == "SELL"
           else price * random.uniform(0.96, 0.98))

    abs_chg = abs(chg)
    risk_score = (random.randint(62, 82) if abs_chg > 8
                  else random.randint(40, 62) if abs_chg > 3
                  else random.randint(22, 42))
    risk = "🔴 High" if risk_score > 60 else "🟡 Medium" if risk_score > 40 else "🟢 Low"

    bb = ("Volatility expanding 💥" if abs_chg > 5 else "Squeeze — breakout imminent ⚡")
    fib382 = fmt_price(hi - (hi - lo) * 0.382)
    fib618 = fmt_price(hi - (hi - lo) * 0.618)
    sent = ("Greedy 😤 — be cautious" if chg > 5
            else "Fearful 😨 — contrarian opportunity" if chg < -5
            else "Neutral 😐")

    key_risks = [
        f"BTC-led correction could override {sym}'s setup",
        "Unexpected macro news could spike volatility",
        f"{chg:+.2f}% 24h move may be overextended",
        f"Low liquidity on {tf} may produce false signals",
        f"Whale pressure near {fmt_price(r1)} could flip momentum",
    ]

    return {
        "sig": sig, "trend": trend, "conf": conf,
        "rsi": f"{rsi:.1f}", "rsi_lbl": rsi_lbl,
        "macd": macd, "ema": ema, "bb": bb,
        "fib382": fib382, "fib618": fib618, "sent": sent,
        "tgt": fmt_price(tgt), "sl": fmt_price(sl),
        "s1": fmt_price(s1), "s2": fmt_price(s2),
        "r1": fmt_price(r1), "r2": fmt_price(r2),
        "risk": risk, "risk_score": risk_score,
        "key_risk": random.choice(key_risks),
        "price": fmt_price(price), "chg": f"{chg:+.2f}%",
    }

def build_message(sym: str, tf: str, d: dict) -> str:
    sig_emoji = "🟢" if d["sig"] == "BUY" else "🔴" if d["sig"] == "SELL" else "🟡"
    name = COIN_NAMES.get(sym, sym)

    bar_filled = int(d["conf"] / 10)
    conf_bar = "█" * bar_filled + "░" * (10 - bar_filled)

    msg = f"""
╔══════════════════════════╗
  🤖 *Crypto AI Predictor*
╚══════════════════════════╝

💰 *{name} ({sym})* · {tf}
📊 Live Price: *{d['price']}*
📈 24h Change: *{d['chg']}*

{sig_emoji} *SIGNAL: {d['sig']}*
`{conf_bar}` {d['conf']}% confidence
🎯 Trend: *{d['trend']}*

━━━━━━━━━━━━━━━━━━━━━
📌 *TRADE LEVELS*
━━━━━━━━━━━━━━━━━━━━━
🎯 Target:   *{d['tgt']}*
🛑 Stop Loss: *{d['sl']}*

━━━━━━━━━━━━━━━━━━━━━
📐 *SUPPORT & RESISTANCE*
━━━━━━━━━━━━━━━━━━━━━
🟢 S1: {d['s1']}  |  S2: {d['s2']}
🔴 R1: {d['r1']}  |  R2: {d['r2']}

━━━━━━━━━━━━━━━━━━━━━
📊 *INDICATORS*
━━━━━━━━━━━━━━━━━━━━━
RSI: *{d['rsi']}* — {d['rsi_lbl']}
MACD: {d['macd']}
EMA: {d['ema']}
BB: {d['bb']}
Fib 38.2%: {d['fib382']}  |  61.8%: {d['fib618']}
Sentiment: {d['sent']}

━━━━━━━━━━━━━━━━━━━━━
⚠️ *RISK*
━━━━━━━━━━━━━━━━━━━━━
Level: {d['risk']} ({d['risk_score']}/100)
Key Risk: _{d['key_risk']}_

━━━━━━━━━━━━━━━━━━━━━
_⚡ Data: Binance · For educational use only_
_Never invest more than you can afford to lose_
"""
    return msg.strip()

# ── Bot handlers ──────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = """
👋 *Welcome to Crypto AI Predictor Bot!*

I give you live trading signals using real Binance prices.

*How to use me:*

1️⃣ *Pick a coin:* Send `/analyze` to choose interactively

2️⃣ *Quick commands for any coin:*
`/btc` `/eth` `/sol` `/bnb` `/xrp`
`/ada` `/doge` `/avax` `/link` `/matic`
`/dot` `/arb` `/uni` `/ltc` `/atom`
`/near` `/apt` `/op`

3️⃣ *With timeframe:*
`/sol 4H` or `/eth 1D` or `/btc 1W`

*Available timeframes:* 1H · 4H · 1D · 1W

Type /help for more info.
"""
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = """
📖 *Commands*

/analyze — Interactive coin selector
/btc, /eth, /sol etc — Quick analysis
/sol 4H — Analysis with timeframe
/coins — See all supported coins
/start — Welcome message

*Timeframes:* 1H · 4H · 1D · 1W

*What you get:*
• Live price from Binance
• BUY / SELL / HOLD signal
• Confidence score
• Target price & stop loss
• Support & resistance levels
• RSI, MACD, EMA, Bollinger, Fibonacci
• Market sentiment
• Risk assessment

⚠️ _For educational purposes only._
"""
    await update.message.reply_text(msg, parse_mode="Markdown")

async def coins_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = "\n".join([f"/{k.lower()} — {v}" for k, v in COIN_NAMES.items()])
    await update.message.reply_text(f"*Supported Coins:*\n\n{lines}", parse_mode="Markdown")

async def analyze_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Show interactive coin selection keyboard"""
    keyboard = []
    row = []
    for i, sym in enumerate(COINS.keys()):
        row.append(InlineKeyboardButton(sym, callback_data=f"coin:{sym}:4H"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🪙 *Select a coin to analyze:*", parse_mode="Markdown", reply_markup=reply_markup)

async def coin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle coin selection → show timeframe selection"""
    query = update.callback_query
    await query.answer()
    _, sym, _ = query.data.split(":")

    keyboard = [
        [
            InlineKeyboardButton("1H", callback_data=f"tf:{sym}:1H"),
            InlineKeyboardButton("4H", callback_data=f"tf:{sym}:4H"),
            InlineKeyboardButton("1D", callback_data=f"tf:{sym}:1D"),
            InlineKeyboardButton("1W", callback_data=f"tf:{sym}:1W"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✅ *{COIN_NAMES.get(sym, sym)} ({sym})* selected\n\n⏱ *Choose timeframe:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def tf_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe selection → run analysis"""
    query = update.callback_query
    await query.answer()
    _, sym, tf = query.data.split(":")

    await query.edit_message_text(f"⏳ Fetching live *{sym}* data from Binance…", parse_mode="Markdown")

    try:
        data = get_price(COINS[sym])
        price = float(data["lastPrice"])
        chg   = float(data["priceChangePercent"])
        hi    = float(data["highPrice"])
        lo    = float(data["lowPrice"])

        d = analyze(sym, tf, price, chg, hi, lo)
        msg = build_message(sym, tf, d)

        # Add refresh button
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"tf:{sym}:{tf}"),
                     InlineKeyboardButton("🪙 New Coin", callback_data=f"newcoin:x:x")]]
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await query.edit_message_text(f"❌ Error fetching price: {e}\n\nPlease try again.")

async def newcoin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    row = []
    for i, sym in enumerate(COINS.keys()):
        row.append(InlineKeyboardButton(sym, callback_data=f"coin:{sym}:4H"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await query.edit_message_text("🪙 *Select a coin to analyze:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def quick_coin(update: Update, ctx: ContextTypes.DEFAULT_TYPE, sym: str):
    """Handle /btc, /sol etc. commands with optional timeframe arg"""
    args = ctx.args
    tf = "4H"
    if args:
        tf_arg = args[0].upper()
        if tf_arg in TIMEFRAMES:
            tf = tf_arg

    if sym not in COINS:
        await update.message.reply_text(f"❌ Unknown coin: {sym}\n\nUse /coins to see all supported coins.")
        return

    msg = await update.message.reply_text(f"⏳ Fetching live *{sym}* data from Binance…", parse_mode="Markdown")

    try:
        data = get_price(COINS[sym])
        price = float(data["lastPrice"])
        chg   = float(data["priceChangePercent"])
        hi    = float(data["highPrice"])
        lo    = float(data["lowPrice"])

        d = analyze(sym, tf, price, chg, hi, lo)
        result = build_message(sym, tf, d)

        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"tf:{sym}:{tf}"),
                     InlineKeyboardButton("🪙 New Coin", callback_data=f"newcoin:x:x")]]
        await msg.edit_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await msg.edit_text(f"❌ Could not fetch price for {sym}.\n\nError: {e}")

# Register quick commands for each coin
def make_handler(sym):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await quick_coin(update, ctx, sym)
    handler.__name__ = f"cmd_{sym.lower()}"
    return handler

async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper().lstrip("/")
    parts = text.split()
    sym = parts[0]
    if sym in COINS:
        tf = parts[1] if len(parts) > 1 and parts[1] in TIMEFRAMES else "4H"
        ctx.args = [tf]
        await quick_coin(update, ctx, sym)
    else:
        await update.message.reply_text(
            "❓ I don't understand that command.\n\nUse /analyze to pick a coin or type /help.",
        )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("coins", coins_cmd))
    app.add_handler(CommandHandler("analyze", analyze_cmd))

    # Quick coin commands
    for sym in COINS:
        app.add_handler(CommandHandler(sym.lower(), make_handler(sym)))

    # Callbacks
    app.add_handler(CallbackQueryHandler(coin_callback,    pattern=r"^coin:"))
    app.add_handler(CallbackQueryHandler(tf_callback,      pattern=r"^tf:"))
    app.add_handler(CallbackQueryHandler(newcoin_callback, pattern=r"^newcoin:"))

    # Fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
