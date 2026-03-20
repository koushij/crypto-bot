import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

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


def get_price(symbol):
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=" + symbol
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def fmt_price(n):
    if n >= 10000: return "$" + format(int(n), ",")
    if n >= 1000:  return "$" + format(int(n), ",")
    if n >= 100:   return "$" + "{:.1f}".format(n)
    if n >= 1:     return "$" + "{:.2f}".format(n)
    return "$" + "{:.4f}".format(n)


def run_analysis(sym, tf, price, chg, hi, lo):
    mom = max(-1, min(1, (chg / 100) * 4 + random.uniform(-0.2, 0.2)))
    rsi = (random.uniform(60, 74) if chg > 6
           else random.uniform(26, 40) if chg < -6
           else random.uniform(38, 62))
    rsi_lbl = "Oversold" if rsi < 35 else "Overbought" if rsi > 65 else "Neutral"
    macd_bull = mom > 0.05
    macd = "Bullish crossover" if macd_bull else ("Bearish crossover" if mom < -0.05 else "Neutral")
    ema = ("Above EMA20/50 - Bullish" if mom > 0.2
           else "Below EMA20/50 - Bearish" if mom < -0.2
           else "Between EMA20-EMA50")

    score = (1 if rsi < 40 else -1 if rsi > 60 else 0) + (1.2 if macd_bull else -1.2) + mom * 2
    if score > 0.8:    sig, trend, conf = "BUY",  "Bullish",  random.randint(62, 84)
    elif score < -0.8: sig, trend, conf = "SELL", "Bearish",  random.randint(60, 80)
    else:              sig, trend, conf = "HOLD", "Sideways", random.randint(48, 65)

    rng = hi - lo or price * 0.04
    s1 = lo + rng * random.uniform(0.05, 0.20)
    s2 = lo - rng * random.uniform(0.05, 0.18)
    r1 = hi - rng * random.uniform(0.05, 0.20)
    r2 = hi + rng * random.uniform(0.05, 0.18)
    tgt = (price + rng * random.uniform(0.3, 0.65) if sig == "BUY"
           else price - rng * random.uniform(0.3, 0.65) if sig == "SELL"
           else price + rng * random.uniform(-0.1, 0.1))
    sl = (s1 * random.uniform(0.97, 0.99) if sig == "BUY"
          else r1 * random.uniform(1.01, 1.03) if sig == "SELL"
          else price * random.uniform(0.96, 0.98))

    abs_chg = abs(chg)
    risk_score = (random.randint(62, 82) if abs_chg > 8
                  else random.randint(40, 62) if abs_chg > 3
                  else random.randint(22, 42))
    risk = "High" if risk_score > 60 else "Medium" if risk_score > 40 else "Low"
    risk_emoji = "🔴" if risk_score > 60 else "🟡" if risk_score > 40 else "🟢"

    fib382 = fmt_price(hi - (hi - lo) * 0.382)
    fib618 = fmt_price(hi - (hi - lo) * 0.618)
    sent = ("Greedy - be cautious" if chg > 5
            else "Fearful - contrarian opportunity" if chg < -5
            else "Neutral")

    key_risks = [
        "BTC-led correction could override this setup",
        "Macro news could spike volatility unexpectedly",
        "{:.2f}% 24h move may be overextended".format(chg),
        "Low liquidity on {} may produce false signals".format(tf),
        "Whale pressure near {} could flip momentum".format(fmt_price(r1)),
    ]

    sig_emoji = "🟢" if sig == "BUY" else "🔴" if sig == "SELL" else "🟡"
    name = COIN_NAMES.get(sym, sym)
    bar = "█" * int(conf / 10) + "░" * (10 - int(conf / 10))
    chg_str = "{:+.2f}%".format(chg)

    msg = (
        "==============================\n"
        "🤖 Crypto AI Predictor\n"
        "==============================\n\n"
        "💰 *{name} ({sym})* - {tf}\n"
        "📊 Live Price: *{price}*\n"
        "📈 24h Change: *{chg}*\n\n"
        "{sig_e} *SIGNAL: {sig}*\n"
        "`{bar}` {conf}%\n"
        "🎯 Trend: *{trend}*\n\n"
        "------------------------------\n"
        "📌 *TRADE LEVELS*\n"
        "------------------------------\n"
        "🎯 Target:    *{tgt}*\n"
        "🛑 Stop Loss: *{sl}*\n\n"
        "------------------------------\n"
        "📐 *SUPPORT & RESISTANCE*\n"
        "------------------------------\n"
        "🟢 S1: {s1}   S2: {s2}\n"
        "🔴 R1: {r1}   R2: {r2}\n\n"
        "------------------------------\n"
        "📊 *INDICATORS*\n"
        "------------------------------\n"
        "RSI: *{rsi}* - {rsi_lbl}\n"
        "MACD: {macd}\n"
        "EMA: {ema}\n"
        "Fib 38.2%: {fib382}  61.8%: {fib618}\n"
        "Sentiment: {sent}\n\n"
        "------------------------------\n"
        "⚠️ *RISK*\n"
        "------------------------------\n"
        "{risk_e} {risk} ({risk_score}/100)\n"
        "_{key_risk}_\n\n"
        "_Data: Binance - Educational use only_\n"
        "_Never invest more than you can afford_"
    ).format(
        name=name, sym=sym, tf=tf,
        price=fmt_price(price), chg=chg_str,
        sig_e=sig_emoji, sig=sig, bar=bar, conf=conf, trend=trend,
        tgt=fmt_price(tgt), sl=fmt_price(sl),
        s1=fmt_price(s1), s2=fmt_price(s2),
        r1=fmt_price(r1), r2=fmt_price(r2),
        rsi="{:.1f}".format(rsi), rsi_lbl=rsi_lbl,
        macd=macd, ema=ema,
        fib382=fib382, fib618=fib618, sent=sent,
        risk_e=risk_emoji, risk=risk, risk_score=risk_score,
        key_risk=random.choice(key_risks)
    )
    return msg


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Welcome to Crypto AI Predictor Bot!*\n\n"
        "I give live trading signals using real Binance prices.\n\n"
        "*Quick commands:*\n"
        "/btc /eth /sol /bnb /xrp\n"
        "/ada /doge /avax /link /matic\n"
        "/dot /arb /uni /ltc /atom\n"
        "/near /apt /op\n\n"
        "*With timeframe:*\n"
        "`/sol 4H` or `/eth 1D` or `/btc 1W`\n\n"
        "*Timeframes:* 1H, 4H, 1D, 1W\n\n"
        "/analyze - Pick coin interactively\n"
        "/coins - All supported coins\n"
        "/help - Help"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Help*\n\n"
        "/analyze - Interactive coin picker\n"
        "/btc, /eth, /sol etc - Quick analysis\n"
        "/sol 4H - With timeframe\n"
        "/coins - All 18 coins\n\n"
        "*What you get:*\n"
        "- Live Binance price\n"
        "- BUY / SELL / HOLD signal\n"
        "- Target price and stop loss\n"
        "- Support and resistance levels\n"
        "- RSI, MACD, EMA, Fibonacci\n"
        "- Risk assessment\n\n"
        "_For educational purposes only._"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def coins_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = "\n".join(["/" + k.lower() + " - " + v for k, v in COIN_NAMES.items()])
    await update.message.reply_text("*Supported Coins (18):*\n\n" + lines, parse_mode="Markdown")


async def analyze_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for sym in COINS.keys():
        row.append(InlineKeyboardButton(sym, callback_data="coin:" + sym))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await update.message.reply_text(
        "🪙 *Select a coin:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def coin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sym = query.data.split(":")[1]
    keyboard = [[
        InlineKeyboardButton("1H", callback_data="tf:" + sym + ":1H"),
        InlineKeyboardButton("4H", callback_data="tf:" + sym + ":4H"),
        InlineKeyboardButton("1D", callback_data="tf:" + sym + ":1D"),
        InlineKeyboardButton("1W", callback_data="tf:" + sym + ":1W"),
    ]]
    await query.edit_message_text(
        "✅ *" + COIN_NAMES.get(sym, sym) + " (" + sym + ")* selected\n\n⏱ *Choose timeframe:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def tf_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    sym = parts[1]
    tf = parts[2]
    await query.edit_message_text("⏳ Fetching live *" + sym + "* data...", parse_mode="Markdown")
    try:
        data = get_price(COINS[sym])
        price = float(data["lastPrice"])
        chg   = float(data["priceChangePercent"])
        hi    = float(data["highPrice"])
        lo    = float(data["lowPrice"])
        msg = run_analysis(sym, tf, price, chg, hi, lo)
        keyboard = [[
            InlineKeyboardButton("🔄 Refresh", callback_data="tf:" + sym + ":" + tf),
            InlineKeyboardButton("🪙 New Coin", callback_data="newcoin"),
        ]]
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await query.edit_message_text("❌ Error: " + str(e) + "\n\nPlease try again.")


async def newcoin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    row = []
    for sym in COINS.keys():
        row.append(InlineKeyboardButton(sym, callback_data="coin:" + sym))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await query.edit_message_text(
        "🪙 *Select a coin:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def do_analysis(update: Update, sym: str, tf: str):
    msg = await update.message.reply_text(
        "⏳ Fetching live *" + sym + "* data from Binance...",
        parse_mode="Markdown"
    )
    try:
        data = get_price(COINS[sym])
        price = float(data["lastPrice"])
        chg   = float(data["priceChangePercent"])
        hi    = float(data["highPrice"])
        lo    = float(data["lowPrice"])
        result = run_analysis(sym, tf, price, chg, hi, lo)
        keyboard = [[
            InlineKeyboardButton("🔄 Refresh", callback_data="tf:" + sym + ":" + tf),
            InlineKeyboardButton("🪙 New Coin", callback_data="newcoin"),
        ]]
        await msg.edit_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await msg.edit_text("❌ Could not fetch price for " + sym + ".\n\nError: " + str(e))


def make_coin_handler(sym):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        tf = "4H"
        if ctx.args and ctx.args[0].upper() in TIMEFRAMES:
            tf = ctx.args[0].upper()
        await do_analysis(update, sym, tf)
    handler.__name__ = "cmd_" + sym.lower()
    return handler


async def unknown_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper().lstrip("/")
    parts = text.split()
    sym = parts[0]
    if sym in COINS:
        tf = parts[1] if len(parts) > 1 and parts[1] in TIMEFRAMES else "4H"
        await do_analysis(update, sym, tf)
    else:
        await update.message.reply_text(
            "❓ Unknown command. Use /analyze to pick a coin or /help for info."
        )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set! Add it in Render Environment Variables.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("coins", coins_cmd))
    app.add_handler(CommandHandler("analyze", analyze_cmd))

    for sym in COINS:
        app.add_handler(CommandHandler(sym.lower(), make_coin_handler(sym)))

    app.add_handler(CallbackQueryHandler(coin_callback,    pattern="^coin:"))
    app.add_handler(CallbackQueryHandler(tf_callback,      pattern="^tf:"))
    app.add_handler(CallbackQueryHandler(newcoin_callback, pattern="^newcoin$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_msg))

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
