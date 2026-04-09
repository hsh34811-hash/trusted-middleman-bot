"""
الميزات الجديدة:
1. تحويل العملات (TON ↔ USD ↔ EGP)
2. تنبيه السعر
3. تحقق من وسيط
4. Blacklist
5. تقييم الوسطاء
6. سجل العمليات
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import load_db, save_db, get_emoji
from utils.helpers import ce, _utf16_len, btn
from config.settings import OWNER_ID

logger = logging.getLogger(__name__)

# ─── سجل العمليات ─────────────────────────────────────────
def log_action(action: str, by: int, details: str = ""):
    db = load_db()
    if "logs" not in db:
        db["logs"] = []
    db["logs"].append({
        "action": action,
        "by": by,
        "details": details,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    db["logs"] = db["logs"][-100:]  # احتفظ بآخر 100 عملية فقط
    save_db(db)


# ─── Blacklist ────────────────────────────────────────────
def get_blacklist() -> list:
    return load_db().get("blacklist", [])

def add_to_blacklist(username: str, reason: str, by: int):
    db = load_db()
    if "blacklist" not in db:
        db["blacklist"] = []
    username = username.lstrip("@").lower()
    if not any(b["username"] == username for b in db["blacklist"]):
        db["blacklist"].append({
            "username": username,
            "reason": reason,
            "added_by": by,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_db(db)
        log_action("blacklist_add", by, f"@{username} — {reason}")
        return True
    return False

def remove_from_blacklist(username: str, by: int) -> bool:
    db = load_db()
    username = username.lstrip("@").lower()
    before = len(db.get("blacklist", []))
    db["blacklist"] = [b for b in db.get("blacklist", []) if b["username"] != username]
    if len(db["blacklist"]) < before:
        save_db(db)
        log_action("blacklist_remove", by, f"@{username}")
        return True
    return False

def is_blacklisted(username: str) -> dict | None:
    username = username.lstrip("@").lower()
    for b in get_blacklist():
        if b["username"] == username:
            return b
    return None


# ─── تقييم الوسطاء ───────────────────────────────────────
def add_rating(username: str, user_id: int, stars: int) -> dict:
    db = load_db()
    if "ratings" not in db:
        db["ratings"] = {}
    username = username.lstrip("@").lower()
    if username not in db["ratings"]:
        db["ratings"][username] = []
    # منع التقييم المكرر من نفس المستخدم
    db["ratings"][username] = [r for r in db["ratings"][username] if r["user_id"] != user_id]
    db["ratings"][username].append({"user_id": user_id, "stars": stars, "date": datetime.now().strftime("%Y-%m-%d")})
    save_db(db)
    return get_middleman_rating(username)

def get_middleman_rating(username: str) -> dict:
    username = username.lstrip("@").lower()
    ratings = load_db().get("ratings", {}).get(username, [])
    if not ratings:
        return {"avg": 0, "count": 0}
    avg = round(sum(r["stars"] for r in ratings) / len(ratings), 1)
    return {"avg": avg, "count": len(ratings)}


# ─── تنبيهات السعر ───────────────────────────────────────
def add_price_alert(user_id: int, target: float, direction: str):
    """direction: 'above' أو 'below'"""
    db = load_db()
    if "alerts" not in db:
        db["alerts"] = []
    db["alerts"].append({"user_id": user_id, "target": target, "direction": direction, "active": True})
    save_db(db)

def get_active_alerts() -> list:
    return [a for a in load_db().get("alerts", []) if a.get("active")]

def deactivate_alert(user_id: int, target: float):
    db = load_db()
    for a in db.get("alerts", []):
        if a["user_id"] == user_id and a["target"] == target:
            a["active"] = False
    save_db(db)


# ─── رسالة تحقق من وسيط ──────────────────────────────────
def build_verify_message(username: str, middlemen: list, super_m: dict | None) -> tuple[str, list]:
    from telegram import MessageEntity
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    uname = username.lstrip("@").lower()
    is_super = super_m and super_m.get("username", "").lower() == uname
    is_trusted = any(m["username"].lower() == uname for m in middlemen) or is_super
    bl = is_blacklisted(uname)
    rating = get_middleman_rating(uname)

    if bl:
        add("🚫", e["banned"])
        add(f" @{username} — محظور ومُبلَّغ عنه!\n\n")
        add("❌", e["untrusted"])
        add(f" السبب: {bl['reason']}\n")
        add("📅", e["calendar"])
        add(f" تاريخ الإضافة: {bl['date']}")
    elif is_trusted:
        add("✅", e["trusted"])
        add(f" @{username} — وسيط موثوق\n")
        if is_super:
            add("👑", e["btn_crown"])
            add(" الوسيط الأعلى موثوقية\n")
        if rating["count"] > 0:
            add("⭐", e["rating"])
            add(f" التقييم: {rating['avg']}/5 ({rating['count']} تقييم)")
    else:
        add("❌", e["untrusted"])
        add(f" @{username} — غير موجود في قائمة الوسطاء الموثوقين\n\n")
        add("⚠️", e["warn"])
        add(" تعامل بحذر!")

    return "".join(parts), entities


# ─── رسالة تحويل العملات ─────────────────────────────────
def build_convert_message(amount: float, from_cur: str, price_data: dict) -> tuple[str, list]:
    from telegram import MessageEntity
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    usd_price = price_data["usd"]
    egp_price = price_data["egp"]

    add("🔄", e["convert"])
    add(" تحويل العملات\n\n")

    if from_cur == "ton":
        total_usd = round(amount * usd_price, 2)
        total_egp = round(amount * egp_price, 2)
        s = cur
        add(f"{amount:g} TON ")
        add("➡️", e["arrow"])
        add(f" {total_usd} USD ")
        add("🇺🇸", e["flag_us"]); add("\n")
        entities.append(MessageEntity(type="blockquote", offset=s, length=cur - s))
        s = cur
        add(f"{amount:g} TON ")
        add("➡️", e["arrow"])
        add(f" {total_egp} EGP ")
        add("🇪🇬", e["flag_eg"]); add("\n")
        entities.append(MessageEntity(type="blockquote", offset=s, length=cur - s))

    elif from_cur == "usd":
        total_ton = round(amount / usd_price, 4)
        total_egp = round(amount * (egp_price / usd_price), 2)
        s = cur
        add(f"{amount:g} USD ")
        add("➡️", e["arrow"])
        add(f" {total_ton} TON\n")
        entities.append(MessageEntity(type="blockquote", offset=s, length=cur - s))
        s = cur
        add(f"{amount:g} USD ")
        add("➡️", e["arrow"])
        add(f" {total_egp} EGP ")
        add("🇪🇬", e["flag_eg"]); add("\n")
        entities.append(MessageEntity(type="blockquote", offset=s, length=cur - s))

    elif from_cur == "egp":
        total_ton = round(amount / egp_price, 4)
        total_usd = round(amount / (egp_price / usd_price), 2)
        s = cur
        add(f"{amount:g} EGP ")
        add("➡️", e["arrow"])
        add(f" {total_ton} TON\n")
        entities.append(MessageEntity(type="blockquote", offset=s, length=cur - s))
        s = cur
        add(f"{amount:g} EGP ")
        add("➡️", e["arrow"])
        add(f" {total_usd} USD ")
        add("🇺🇸", e["flag_us"]); add("\n")
        entities.append(MessageEntity(type="blockquote", offset=s, length=cur - s))

    return "".join(parts), entities


async def convert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحويل العملات — مثلاً: 100 دولار، 500 جنيه، 10 ton"""
    import re
    from handlers.ton_price import fetch_ton_price
    message = update.message
    if not message:
        return
    text = message.text.lower().strip()

    patterns = [
        (r"(\d+(?:\.\d+)?)\s*(?:ton|تون|طون)", "ton"),
        (r"(\d+(?:\.\d+)?)\s*(?:usd|دولار|dollar)", "usd"),
        (r"(\d+(?:\.\d+)?)\s*(?:egp|جنيه|pound)", "egp"),
    ]
    amount, from_cur = None, None
    for pattern, cur in patterns:
        m = re.search(pattern, text)
        if m:
            amount = float(m.group(1))
            from_cur = cur
            break

    if not amount:
        return

    price_data = await fetch_ton_price()
    if not price_data:
        await message.reply_text("⚠️ تعذر جلب السعر الآن.")
        return

    text_msg, entities = build_convert_message(amount, from_cur, price_data)
    from utils.helpers import build_ton_keyboard
    await message.reply_text(text_msg, entities=entities, reply_markup=build_ton_keyboard())


# ─── Handlers ─────────────────────────────────────────────
async def verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحقق من وسيط — /verify @username أو كتابة @username في الخاص"""
    message = update.message
    if not message:
        return
    text = message.text.strip()
    # استخراج اليوزرنيم
    import re
    match = re.search(r"@(\w+)", text)
    if not match:
        await message.reply_text("أرسل يوزرنيم الوسيط بالشكل: @username")
        return
    username = match.group(1)
    from database.db import get_middlemen, get_super_middleman
    middlemen = get_middlemen()
    super_m = get_super_middleman()
    text_msg, entities = build_verify_message(username, middlemen, super_m)
    await message.reply_text(text_msg, entities=entities)


async def check_price_alerts(context: ContextTypes.DEFAULT_TYPE):
    """يُشغَّل دورياً للتحقق من تنبيهات السعر"""
    from handlers.ton_price import fetch_ton_price
    price_data = await fetch_ton_price()
    if not price_data:
        return
    current = price_data["usd"]
    alerts = get_active_alerts()
    for alert in alerts:
        triggered = (
            (alert["direction"] == "above" and current >= alert["target"]) or
            (alert["direction"] == "below" and current <= alert["target"])
        )
        if triggered:
            try:
                e = get_emoji()
                direction_text = "وصل لـ" if alert["direction"] == "above" else "نزل لـ"
                await context.bot.send_message(
                    chat_id=alert["user_id"],
                    text=f"🔔 تنبيه السعر!\n\nسعر TON {direction_text} {alert['target']} USD\nالسعر الحالي: {current} USD"
                )
                deactivate_alert(alert["user_id"], alert["target"])
            except Exception as ex:
                logger.warning(f"Alert send error: {ex}")
