"""
هاندلر المجموعات
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import TRIGGER_KEYWORDS, TON_KEYWORDS
from database.db import (
    get_middlemen, get_super_middleman,
    is_auto_reply_enabled, get_group_settings,
    increment_stat
)
from middlewares.cooldown import is_on_cooldown, set_cooldown
from utils.helpers import build_middleman_message, build_middleman_keyboard

logger = logging.getLogger(__name__)


async def _auto_delete(message, delay: int = 60):
    """حذف الرسالة تلقائياً بعد delay ثانية"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    if message.chat.type == "private":
        return

    text_lower = message.text.lower().strip()

    # ── تحقق من وسيط تلقائي لو كتب @username ────────────
    import re as _re
    if _re.match(r"^@\w+$", message.text.strip()):
        from handlers.features import build_verify_message, is_blacklisted
        from utils.helpers import build_rating_keyboard
        username = message.text.strip().lstrip("@")
        middlemen_list = get_middlemen()
        super_m = get_super_middleman()
        logger.info(f"[verify] username={username} middlemen={middlemen_list} super={super_m}")
        text_msg, entities = build_verify_message(username, middlemen_list, super_m)
        keyboard = None if is_blacklisted(username) else build_rating_keyboard(username)
        sent = await message.reply_text(text_msg, entities=entities,
                                        reply_markup=keyboard,
                                        reply_to_message_id=message.message_id)
        asyncio.create_task(_auto_delete(sent))
        return

    # ── سعر TON ───────────────────────────────────────────
    if any(kw.lower() in text_lower for kw in TON_KEYWORDS):
        from handlers.ton_price import fetch_ton_price, build_ton_message, extract_ton_amount
        from utils.helpers import build_ton_keyboard
        amount = extract_ton_amount(text_lower)
        price_data = await fetch_ton_price()
        if price_data:
            increment_stat("total_ton_requests")
            text, entities = build_ton_message(price_data, amount)
            await message.reply_text(
                text,
                entities=entities,
                reply_markup=build_ton_keyboard(),
                reply_to_message_id=message.message_id,
            )
        else:
            await message.reply_text("⚠️ تعذر جلب السعر الآن، حاول مرة أخرى.")
        return

    # ── كلمات الوسيط ──────────────────────────────────────
    if not any(kw.lower() in text_lower for kw in TRIGGER_KEYWORDS):
        return

    chat_id = message.chat_id
    user_id = message.from_user.id

    if not is_auto_reply_enabled():
        return
    if not get_group_settings(chat_id).get("auto_reply", True):
        return
    if is_on_cooldown(chat_id, user_id):
        return

    middlemen = get_middlemen()
    super_middleman = get_super_middleman()
    msg_text, entities = build_middleman_message(middlemen, super_middleman)
    keyboard = build_middleman_keyboard()

    await message.reply_text(
        msg_text,
        entities=entities,
        reply_markup=keyboard,
        reply_to_message_id=message.message_id,
    )
    set_cooldown(chat_id, user_id)
    increment_stat("total_replies")


# ─── Callbacks ────────────────────────────────────────────
async def middleman_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    middlemen = get_middlemen()
    if not middlemen:
        await query.message.reply_text("لا يوجد وسطاء مسجلون حالياً.")
        return
    from utils.helpers import build_middleman_message, build_middleman_keyboard
    super_m = get_super_middleman()
    text, entities = build_middleman_message(middlemen, super_m)
    await query.message.reply_text(text, entities=entities, reply_markup=build_middleman_keyboard())


async def super_middleman_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    super_m = get_super_middleman()
    if not super_m:
        await query.message.reply_text("لم يتم تعيين وسيط أعلى بعد.")
        return
    from utils.helpers import build_super_middleman_message
    text, entities = build_super_middleman_message(super_m)
    sent = await query.message.reply_text(text, entities=entities)
    asyncio.create_task(_auto_delete(sent))


async def rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from utils.helpers import build_rules_message
    text, entities = build_rules_message()
    sent = await query.message.reply_text(text, entities=entities)
    asyncio.create_task(_auto_delete(sent))


async def report_scam_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from utils.helpers import build_report_keyboard
    keyboard = build_report_keyboard()
    text = "🚨 للإبلاغ عن نصاب، تواصل مع أحد جهات الإبلاغ أدناه:"
    if not keyboard:
        text = "🚨 للإبلاغ عن نصاب:\nتواصل مع المالك مباشرة وأرسل سجل المحادثة."
    sent = await query.message.reply_text(text, reply_markup=keyboard)
    asyncio.create_task(_auto_delete(sent))


async def contact_middleman_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    middlemen = get_middlemen()
    if not middlemen:
        await query.message.reply_text("لا يوجد وسطاء متاحون حالياً.")
        return
    from utils.helpers import build_contact_message
    text, entities = build_contact_message(middlemen)
    sent = await query.message.reply_text(text, entities=entities)
    asyncio.create_task(_auto_delete(sent))


async def start_ton_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري جلب السعر...")
    from handlers.ton_price import fetch_ton_price, build_ton_message
    from utils.helpers import build_ton_keyboard
    price_data = await fetch_ton_price()
    if not price_data:
        await query.answer("⚠️ تعذر جلب السعر الآن.", show_alert=True)
        return
    text, entities = build_ton_message(price_data)
    await query.message.reply_text(
        text,
        entities=entities,
        reply_markup=build_ton_keyboard(),
    )


async def open_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    from config.settings import OWNER_ID
    from database.db import is_admin
    from utils.helpers import build_owner_panel_keyboard, build_admin_panel_keyboard
    if user_id == OWNER_ID:
        await query.message.reply_text(
            "👑 لوحة تحكم المالك:",
            reply_markup=build_owner_panel_keyboard(),
        )
    elif is_admin(user_id):
        await query.message.reply_text(
            "🔧 لوحة تحكم الأدمن:",
            reply_markup=build_admin_panel_keyboard(),
        )
    else:
        await query.answer("❌ ليس لديك صلاحية.", show_alert=True)


async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """زر الرجوع — يغلق الـ alert"""
    query = update.callback_query
    await query.answer()


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحقق من وسيط — زر أو أمر"""
    # من زر
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text(
            "🔍 أرسل يوزرنيم الوسيط للتحقق منه:\nمثال: @username"
        )
        return
    # من أمر /verify
    if update.message:
        from handlers.features import build_verify_message
        text = update.message.text.strip()
        import re
        match = re.search(r"@(\w+)", text)
        if not match:
            await update.message.reply_text("أرسل يوزرنيم الوسيط:\n/verify @username")
            return
        username = match.group(1)
        middlemen = get_middlemen()
        super_m = get_super_middleman()
        text_msg, entities = build_verify_message(username, middlemen, super_m)
        from utils.helpers import build_rating_keyboard
        from handlers.features import is_blacklisted
        keyboard = None if is_blacklisted(username) else build_rating_keyboard(username)
        await update.message.reply_text(text_msg, entities=entities, reply_markup=keyboard)


async def blacklist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة النصابين"""
    query = update.callback_query
    await query.answer()
    from handlers.features import get_blacklist
    from database.db import get_emoji
    from utils.helpers import ce, _utf16_len
    from telegram import MessageEntity
    bl = get_blacklist()
    if not bl:
        await query.message.reply_text("✅ قائمة النصابين فارغة حالياً.")
        return
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text, eid=None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("🚫", e["banned"])
    add(f" قائمة النصابين ({len(bl)}):\n\n")
    for b in bl:
        add("❌", e["untrusted"])
        add(f" @{b['username']} — {b['reason']}\n")
        add("📅", e["calendar"])
        add(f" {b['date']}\n\n")

    sent = await query.message.reply_text("".join(parts), entities=entities)
    asyncio.create_task(_auto_delete(sent))


async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تقييم وسيط"""
    query = update.callback_query
    await query.answer()
    import re
    match = re.match(r"rate_(\w+)_([1-5])", query.data)
    if not match:
        return
    username, stars = match.group(1), int(match.group(2))
    from handlers.features import add_rating
    result = add_rating(username, query.from_user.id, stars)
    from database.db import get_emoji
    from utils.helpers import ce, _utf16_len
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text, eid=None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("✅", e["trusted"])
    add(f" تم تقييم @{username}\n\n")
    # النجوم بـ custom emoji بعدد الرقم
    for _ in range(stars):
        add("⭐", e["rating"])
    add(f" {stars}/5\n")
    add("⭐", e["rating"])
    add(f" متوسط التقييم: {result['avg']}/5 ({result['count']} تقييم)")
    sent = await query.message.reply_text("".join(parts), entities=entities)
    asyncio.create_task(_auto_delete(sent))
