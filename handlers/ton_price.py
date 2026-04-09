"""
هاندلر سعر TON اللحظي
المصادر:
  1. Binance API  — سعر TON/USDT (الأدق والأسرع)
  2. CoinGecko    — fallback
  3. ExchangeRate-API — سعر USD/EGP الرسمي
"""
import re
import logging
import aiohttp
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import BINANCE_API, COINGECKO_API, EXCHANGERATE_API, TON_KEYWORDS
from database.db import increment_stat
from utils.helpers import build_ton_keyboard

logger = logging.getLogger(__name__)


async def fetch_usd_to_egp() -> float:
    """جلب سعر الدولار بالجنيه المصري من ExchangeRate-API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EXCHANGERATE_API, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data["rates"]["EGP"])
    except Exception:
        pass
    return 50.5  # fallback تقريبي


async def fetch_ton_price() -> dict | None:
    egp_rate = await fetch_usd_to_egp()

    # ── Binance أولاً ──────────────────────────────────────
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BINANCE_API, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usd = round(float(data["price"]), 4)
                    return {"usd": usd, "egp": round(usd * egp_rate, 2), "source": "Binance"}
                logger.warning(f"Binance status: {resp.status}")
    except Exception as ex:
        logger.warning(f"Binance error: {ex}")

    # ── CoinGecko fallback ─────────────────────────────────
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(COINGECKO_API, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ton = data.get("the-open-network", {})
                    usd = round(float(ton["usd"]), 4)
                    egp = round(usd * egp_rate, 2)
                    return {"usd": usd, "egp": egp, "source": "CoinGecko"}
                logger.warning(f"CoinGecko status: {resp.status}")
    except Exception as ex:
        logger.warning(f"CoinGecko error: {ex}")

    return None


def extract_ton_amount(text: str) -> float:
    """
    يستخرج الكمية من النص — مثلاً:
    "28 تون" → 28.0
    "5.5 ton" → 5.5
    "1 تون" → 1.0
    "سعر التون" → 1.0 (افتراضي)
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ton|تون|طون)", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 1.0


def build_ton_message(price_data: dict, amount: float = 1.0) -> tuple[str, list]:
    from telegram import MessageEntity
    from database.db import get_emoji
    from utils.helpers import ce, _utf16_len

    e      = get_emoji()
    usd    = price_data.get("usd", 0)
    egp    = price_data.get("egp", 0)
    source = price_data.get("source", "—")
    now    = datetime.now().strftime("%H:%M:%S")

    # حساب الكمية
    total_usd = round(usd * amount, 4) if amount != 1.0 else usd
    total_egp = round(egp * amount, 2) if amount != 1.0 else egp
    amt_label = f"{amount:g}" if amount != 1.0 else "1"

    entities: list[MessageEntity] = []
    parts:    list[str]           = []
    cur = 0

    def add(text: str, eid: str = None, elen: int = None):
        nonlocal cur
        if eid:
            length = elen if elen else _utf16_len(text)
            entities.append(ce(cur, length, eid))
        parts.append(text)
        cur += _utf16_len(text)

    # ── العنوان ───────────────────────────────────────────
    add("💎", e["ton_gem"], 2)
    if amount != 1.0:
        add(f" سعر {amt_label} TON الآن\n\n")
    else:
        add(" سعر TON الآن\n\n")

    # ── سطر USD ───────────────────────────────────────────
    usd_start = cur
    add(f"{amt_label} TON ")
    add("➡️", e["arrow"], 2)
    add(f" {total_usd} USD ")
    add("🇺🇸", e["flag_us"], 4)
    add("\n")
    entities.append(MessageEntity(type="blockquote", offset=usd_start, length=cur - usd_start))

    # ── سطر EGP ───────────────────────────────────────────
    egp_start = cur
    add(f"{amt_label} TON ")
    add("➡️", e["arrow"], 2)
    add(f" {total_egp} EGP ")
    add("🇪🇬", e["flag_eg"], 4)
    add("\n")
    entities.append(MessageEntity(type="blockquote", offset=egp_start, length=cur - egp_start))

    add("\n")

    # ── وقت التحديث والمصدر ───────────────────────────────
    add("⏰", e["clock"], 1)
    add(f" آخر تحديث: {now}\n")
    add("📡", e["antenna"], 2)
    add(f" المصدر: {source}")

    return "".join(parts), entities


async def ton_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    text_lower = message.text.lower().strip()

    # ── تحويل العملات (دولار/جنيه) ────────────────────────
    from config.settings import CONVERT_KEYWORDS
    if any(kw in text_lower for kw in CONVERT_KEYWORDS):
        from handlers.features import convert_handler
        await convert_handler(update, context)
        return

    # ── تحقق من وسيط ──────────────────────────────────────
    import re
    if re.match(r"^@\w+$", message.text.strip()):
        from handlers.features import build_verify_message, is_blacklisted
        from utils.helpers import build_rating_keyboard
        from database.db import get_middlemen, get_super_middleman
        username = message.text.strip().lstrip("@")
        text_msg, entities = build_verify_message(username, get_middlemen(), get_super_middleman())
        keyboard = None if is_blacklisted(username) else build_rating_keyboard(username)
        await message.reply_text(text_msg, entities=entities, reply_markup=keyboard)
        return

    if not any(kw.lower() in text_lower for kw in TON_KEYWORDS):
        return

    amount = extract_ton_amount(text_lower)
    price_data = await fetch_ton_price()
    if not price_data:
        await message.reply_text("⚠️ تعذر جلب السعر الآن، حاول مرة أخرى لاحقاً.")
        return

    increment_stat("total_ton_requests")
    text, entities = build_ton_message(price_data, amount)
    await message.reply_text(
        text,
        entities=entities,
        reply_markup=build_ton_keyboard(),
        reply_to_message_id=message.message_id,
    )


async def ton_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التحديث...")
    price_data = await fetch_ton_price()
    if not price_data:
        await query.edit_message_text("⚠️ تعذر جلب السعر الآن، حاول مرة أخرى.")
        return
    text, entities = build_ton_message(price_data)
    await query.edit_message_text(
        text,
        entities=entities,
        reply_markup=build_ton_keyboard(),
    )
