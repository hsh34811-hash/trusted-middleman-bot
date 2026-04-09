"""
هاندلر لوحة التحكم - Owner & Admin
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from config.settings import OWNER_ID
from database.db import (
    add_admin, remove_admin, get_admins, is_admin,
    add_middleman, remove_middleman, get_middlemen,
    set_super_middleman, get_super_middleman,
    set_auto_reply, is_auto_reply_enabled,
    update_setting, get_settings, get_stats, increment_stat,
    add_report_contact, remove_report_contact, get_report_contacts,
)
from utils.helpers import build_owner_panel_keyboard, build_admin_panel_keyboard

# حالات المحادثة
(
    WAIT_ADMIN_ID,
    WAIT_REMOVE_ADMIN_ID,
    WAIT_MIDDLEMAN_NAME,
    WAIT_MIDDLEMAN_USERNAME,
    WAIT_REMOVE_MIDDLEMAN,
    WAIT_SUPER_NAME,
    WAIT_SUPER_USERNAME,
    WAIT_EMOJI_KEY,
    WAIT_EMOJI_VALUE,
    WAIT_BLACKLIST_ADD,
    WAIT_BLACKLIST_DEL,
    WAIT_ALERT_PRICE,
    WAIT_REPORT_CONTACT_ADD,
    WAIT_REPORT_CONTACT_DEL,
) = range(14)


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# ─── /start ───────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.helpers import build_start_message, build_start_keyboard
    user_id = update.effective_user.id
    text, entities = build_start_message(update.effective_user.first_name)
    await update.message.reply_text(text, entities=entities, reply_markup=build_start_keyboard(user_id))


# ─── /panel ───────────────────────────────────────────────
async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_owner(user_id):
        await update.message.reply_text("👑 لوحة تحكم المالك:", reply_markup=build_owner_panel_keyboard())
    elif is_admin(user_id):
        await update.message.reply_text("🔧 لوحة تحكم الأدمن:", reply_markup=build_admin_panel_keyboard())
    else:
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول للوحة التحكم.")


# ─── /middlemen ───────────────────────────────────────────
async def middlemen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    middlemen = get_middlemen()
    super_m = get_super_middleman()
    if not middlemen and not super_m:
        await update.message.reply_text("📋 لا يوجد وسطاء مسجلون حالياً.")
        return
    text = "✅ قائمة الوسطاء الموثوقين:\n\n"
    for i, m in enumerate(middlemen, 1):
        text += f"{i}. {m['name']} — @{m['username']}\n"
    if super_m:
        text += f"\n⭐️ الوسيط الأعلى موثوقية:\n👑 {super_m['name']} — @{super_m['username']}\n"
    await update.message.reply_text(text)


# ─── /ton ─────────────────────────────────────────────────
async def ton_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.ton_price import fetch_ton_price, build_ton_message
    from utils.helpers import build_ton_keyboard
    price_data = await fetch_ton_price()
    if not price_data:
        await update.message.reply_text("⚠️ تعذر جلب السعر الآن، حاول مرة أخرى.")
        return
    increment_stat("total_ton_requests")
    text, entities = build_ton_message(price_data)
    await update.message.reply_text(text, entities=entities, reply_markup=build_ton_keyboard())


# ─── ConversationHandler entry: أزرار تحتاج إدخال نص ─────
async def owner_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج فقط الأزرار التي تبدأ conversation (تحتاج إدخال نص من المستخدم)"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if not (is_owner(user_id) or is_admin(user_id)):
        await query.answer("❌ غير مصرح لك.", show_alert=True)
        return ConversationHandler.END

    await query.answer()

    if data == "owner_add_admin":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        context.user_data["action"] = "add_admin"
        await query.message.reply_text("📝 أرسل ID المستخدم الذي تريد تعيينه أدمناً:")
        return WAIT_ADMIN_ID

    elif data == "owner_remove_admin":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        admins = get_admins()
        if not admins:
            await query.message.reply_text("لا يوجد أدمنز حالياً.")
            return ConversationHandler.END
        text = "الأدمنز الحاليون:\n" + "\n".join(str(a) for a in admins)
        context.user_data["action"] = "remove_admin"
        await query.message.reply_text(text + "\n\nأرسل ID الأدمن الذي تريد حذفه:")
        return WAIT_REMOVE_ADMIN_ID

    elif data == "owner_add_middleman":
        context.user_data["action"] = "add_middleman"
        await query.message.reply_text("📝 أرسل اسم الوسيط:")
        return WAIT_MIDDLEMAN_NAME

    elif data == "owner_remove_middleman":
        middlemen = get_middlemen()
        if not middlemen:
            await query.message.reply_text("لا يوجد وسطاء حالياً.")
            return ConversationHandler.END
        text = "الوسطاء الحاليون:\n" + "\n".join(f"@{m['username']}" for m in middlemen)
        context.user_data["action"] = "remove_middleman"
        await query.message.reply_text(text + "\n\nأرسل يوزرنيم الوسيط الذي تريد حذفه (بدون @):")
        return WAIT_REMOVE_MIDDLEMAN

    elif data == "owner_set_super":
        context.user_data["action"] = "set_super"
        await query.message.reply_text("📝 أرسل اسم الوسيط الأعلى:")
        return WAIT_SUPER_NAME

    elif data == "owner_edit_emoji":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        from config.settings import EMOJI
        e = get_settings()
        lines = "\n".join(f"{k}: {e.get('emoji_'+k, EMOJI[k])}" for k in EMOJI)
        await query.message.reply_text(
            f"🎨 الإيموجي الحالية:\n\n{lines}\n\n"
            "أرسل المفتاح والـ ID بالشكل:\n"
            "wave 5402498632739996967"
        )
        return WAIT_EMOJI_KEY

    elif data == "admin_add_middleman":
        context.user_data["action"] = "add_middleman"
        await query.message.reply_text("📝 أرسل اسم الوسيط:")
        return WAIT_MIDDLEMAN_NAME

    elif data == "admin_remove_middleman":
        middlemen = get_middlemen()
        if not middlemen:
            await query.message.reply_text("لا يوجد وسطاء حالياً.")
            return ConversationHandler.END
        text = "الوسطاء:\n" + "\n".join(f"@{m['username']}" for m in middlemen)
        context.user_data["action"] = "remove_middleman"
        await query.message.reply_text(text + "\n\nأرسل يوزرنيم الوسيط (بدون @):")
        return WAIT_REMOVE_MIDDLEMAN

    elif data == "owner_add_blacklist":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        context.user_data["action"] = "add_blacklist"
        await query.message.reply_text("📝 أرسل يوزرنيم النصاب والسبب بالشكل:\n@username السبب")
        return WAIT_BLACKLIST_ADD

    elif data == "owner_del_blacklist":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        from handlers.features import get_blacklist
        bl = get_blacklist()
        if not bl:
            await query.message.reply_text("قائمة النصابين فارغة.")
            return ConversationHandler.END
        text = "النصابون:\n" + "\n".join(f"@{b['username']}" for b in bl)
        context.user_data["action"] = "del_blacklist"
        await query.message.reply_text(text + "\n\nأرسل يوزرنيم من تريد حذفه:")
        return WAIT_BLACKLIST_DEL

    elif data == "owner_add_report_contact":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        await query.message.reply_text(
            "📝 أرسل يوزرنيم جهة الإبلاغ والاسم الظاهر بالشكل:\n"
            "@username الاسم\n\n"
            "مثال: @P_X_24 المالك"
        )
        return WAIT_REPORT_CONTACT_ADD

    elif data == "owner_del_report_contact":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return ConversationHandler.END
        contacts = get_report_contacts()
        if not contacts:
            await query.message.reply_text("لا توجد جهات إبلاغ مضافة.")
            return ConversationHandler.END
        text = "جهات الإبلاغ الحالية:\n" + "\n".join(f"@{c['username']} — {c['label']}" for c in contacts)
        await query.message.reply_text(text + "\n\nأرسل يوزرنيم من تريد حذفه:")
        return WAIT_REPORT_CONTACT_DEL

    return ConversationHandler.END


# ─── Simple callbacks: أزرار لا تحتاج إدخال نص ───────────
async def owner_simple_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يعالج الأزرار الفورية في لوحة التحكم:
    stats, groups, ton, enable/disable reply, admin_list, back
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if not (is_owner(user_id) or is_admin(user_id)):
        await query.answer("❌ غير مصرح لك.", show_alert=True)
        return

    await query.answer()

    if data == "owner_enable_reply":
        set_auto_reply(True)
        await query.message.reply_text("✅ تم تفعيل الرد التلقائي.")

    elif data == "owner_disable_reply":
        set_auto_reply(False)
        await query.message.reply_text("❌ تم إيقاف الرد التلقائي.")

    elif data == "owner_remove_super":
        if not is_owner(user_id):
            await query.answer("❌ للمالك فقط.", show_alert=True)
            return
        from database.db import remove_super_middleman, get_super_middleman
        super_m = get_super_middleman()
        if not super_m:
            await query.message.reply_text("لا يوجد وسيط أعلى مُعيَّن حالياً.")
            return
        remove_super_middleman()
        await query.message.reply_text(f"✅ تم حذف الوسيط الأعلى @{super_m['username']}.")

    elif data == "owner_ton":
        from handlers.ton_price import fetch_ton_price, build_ton_message
        from utils.helpers import build_ton_keyboard
        price_data = await fetch_ton_price()
        if not price_data:
            await query.message.reply_text("⚠️ تعذر جلب السعر الآن.")
            return
        increment_stat("total_ton_requests")
        text, entities = build_ton_message(price_data)
        await query.message.reply_text(text, entities=entities, reply_markup=build_ton_keyboard())

    elif data == "owner_stats":
        stats = get_stats()
        from handlers.features import get_blacklist
        from database.db import load_db
        db = load_db()
        ratings = db.get("ratings", {})
        rating_lines = ""
        for uname, reviews in ratings.items():
            if reviews:
                avg = round(sum(r["stars"] for r in reviews) / len(reviews), 1)
                rating_lines += f"  @{uname}: {avg}/5 ({len(reviews)} تقييم)\n"
        bl_count = len(get_blacklist())
        text = (
            "📊 الإحصائيات:\n\n"
            f"إجمالي الردود التلقائية: {stats.get('total_replies', 0)}\n"
            f"إجمالي طلبات سعر TON: {stats.get('total_ton_requests', 0)}\n"
            f"النصابون المحظورون: {bl_count}\n\n"
        )
        if rating_lines:
            text += f"⭐ تقييمات الوسطاء:\n{rating_lines}"
        else:
            text += "⭐ لا توجد تقييمات بعد."
        await query.message.reply_text(text)

    elif data == "owner_groups":
        from database.db import load_db
        db = load_db()
        groups = db.get("groups", {})
        if not groups:
            await query.message.reply_text("لا توجد مجموعات مسجلة بعد.")
            return
        text = f"👥 المجموعات المسجلة: {len(groups)}\n"
        for gid, gsettings in groups.items():
            text += f"\nID: {gid} — الرد التلقائي: {'✅' if gsettings.get('auto_reply', True) else '❌'}"
        await query.message.reply_text(text)

    elif data == "admin_list":
        middlemen = get_middlemen()
        if not middlemen:
            await query.message.reply_text("لا يوجد وسطاء.")
            return
        text = "📋 قائمة الوسطاء:\n\n"
        for i, m in enumerate(middlemen, 1):
            text += f"{i}. {m['name']} — @{m['username']}\n"
        await query.message.reply_text(text)

    elif data == "owner_logs":
        from database.db import load_db
        db = load_db()
        logs = db.get("logs", [])
        if not logs:
            await query.message.reply_text("لا توجد عمليات مسجلة بعد.")
            return
        text = "📋 آخر العمليات:\n\n"
        for entry in reversed(logs[-20:]):
            text += f"• {entry['action']} — {entry['details']}\n  🕐 {entry['time']}\n\n"
        await query.message.reply_text(text)

    elif data in ("owner_back", "admin_back"):
        from utils.helpers import build_start_message, build_start_keyboard
        first_name = query.from_user.first_name
        text, entities = build_start_message(first_name)
        await query.message.reply_text(text, entities=entities, reply_markup=build_start_keyboard(user_id))


# ─── Conversation Steps ───────────────────────────────────
async def receive_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text.strip())
        add_admin(uid)
        await update.message.reply_text(f"✅ تم إضافة {uid} كأدمن.")
    except ValueError:
        await update.message.reply_text("❌ ID غير صحيح.")
    return ConversationHandler.END


async def receive_remove_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text.strip())
        remove_admin(uid)
        await update.message.reply_text(f"✅ تم حذف الأدمن {uid}.")
    except ValueError:
        await update.message.reply_text("❌ ID غير صحيح.")
    return ConversationHandler.END


async def receive_middleman_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["middleman_name"] = update.message.text.strip()
    await update.message.reply_text("📝 أرسل يوزرنيم الوسيط (بدون @):")
    return WAIT_MIDDLEMAN_USERNAME


async def receive_middleman_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    name = context.user_data.get("middleman_name", "وسيط")
    add_middleman(name, username)
    await update.message.reply_text(f"✅ تم إضافة الوسيط {name} (@{username}).")
    return ConversationHandler.END


async def receive_remove_middleman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    remove_middleman(username)
    await update.message.reply_text(f"✅ تم حذف الوسيط @{username}.")
    return ConversationHandler.END


async def receive_super_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["super_name"] = update.message.text.strip()
    await update.message.reply_text("📝 أرسل يوزرنيم الوسيط الأعلى (بدون @):")
    return WAIT_SUPER_USERNAME


async def receive_super_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    name = context.user_data.get("super_name", "وسيط أعلى")
    set_super_middleman(name, username)
    await update.message.reply_text(f"✅ تم تعيين {name} (@{username}) كوسيط أعلى.")
    return ConversationHandler.END


async def receive_emoji_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text("❌ الصيغة غير صحيحة. مثال:\nwave 5402498632739996967")
        return WAIT_EMOJI_KEY
    key, value = parts
    from config.settings import EMOJI
    if key not in EMOJI:
        await update.message.reply_text(f"❌ المفتاح غير صحيح.\nالمفاتيح المتاحة:\n" + ", ".join(EMOJI.keys()))
        return WAIT_EMOJI_KEY
    update_setting(f"emoji_{key}", value)
    await update.message.reply_text(f"✅ تم تحديث إيموجي {key}.")
    return ConversationHandler.END


async def receive_blacklist_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re
    text = update.message.text.strip()
    match = re.match(r"@?(\w+)\s+(.+)", text)
    if not match:
        await update.message.reply_text("❌ الصيغة غير صحيحة. مثال:\n@username نصاب أخذ فلوس")
        return WAIT_BLACKLIST_ADD
    username, reason = match.group(1), match.group(2)
    from handlers.features import add_to_blacklist
    added = add_to_blacklist(username, reason, update.effective_user.id)
    if added:
        await update.message.reply_text(f"✅ تم إضافة @{username} لقائمة النصابين.")
    else:
        await update.message.reply_text(f"⚠️ @{username} موجود بالفعل في القائمة.")
    return ConversationHandler.END


async def receive_blacklist_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    from handlers.features import remove_from_blacklist
    removed = remove_from_blacklist(username, update.effective_user.id)
    if removed:
        await update.message.reply_text(f"✅ تم حذف @{username} من قائمة النصابين.")
    else:
        await update.message.reply_text(f"❌ @{username} غير موجود في القائمة.")
    return ConversationHandler.END


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات عامة للمستخدمين"""
    from database.db import load_db
    from handlers.features import get_blacklist
    db = load_db()
    ratings = db.get("ratings", {})
    stats = get_stats()
    text = "📊 إحصائيات البوت:\n\n"
    text += f"إجمالي الردود: {stats.get('total_replies', 0)}\n"
    text += f"طلبات سعر TON: {stats.get('total_ton_requests', 0)}\n"
    text += f"نصابون محظورون: {len(get_blacklist())}\n\n"
    if ratings:
        text += "⭐ تقييمات الوسطاء:\n"
        for uname, reviews in ratings.items():
            if reviews:
                avg = round(sum(r["stars"] for r in reviews) / len(reviews), 1)
                text += f"  @{uname}: {avg}/5 ({len(reviews)} تقييم)\n"
    else:
        text += "⭐ لا توجد تقييمات بعد."
    await update.message.reply_text(text)


async def receive_report_contact_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re
    text = update.message.text.strip()
    match = re.match(r"@?(\w+)\s*(.*)", text)
    if not match:
        await update.message.reply_text("❌ الصيغة غير صحيحة. مثال:\n@username الاسم")
        return WAIT_REPORT_CONTACT_ADD
    username, label = match.group(1), match.group(2).strip() or match.group(1)
    added = add_report_contact(username, label)
    if added:
        await update.message.reply_text(f"✅ تم إضافة @{username} كجهة إبلاغ.")
    else:
        await update.message.reply_text(f"⚠️ @{username} موجود بالفعل.")
    return ConversationHandler.END


async def receive_report_contact_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    removed = remove_report_contact(username)
    if removed:
        await update.message.reply_text(f"✅ تم حذف @{username} من جهات الإبلاغ.")
    else:
        await update.message.reply_text(f"❌ @{username} غير موجود.")
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END


def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[],
        states={
            WAIT_ADMIN_ID:           [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id)],
            WAIT_REMOVE_ADMIN_ID:    [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_admin_id)],
            WAIT_MIDDLEMAN_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_middleman_name)],
            WAIT_MIDDLEMAN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_middleman_username)],
            WAIT_REMOVE_MIDDLEMAN:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_middleman)],
            WAIT_SUPER_NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_super_name)],
            WAIT_SUPER_USERNAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_super_username)],
            WAIT_EMOJI_KEY:          [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_emoji_value)],
            WAIT_BLACKLIST_ADD:      [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_blacklist_add)],
            WAIT_BLACKLIST_DEL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_blacklist_del)],
            WAIT_REPORT_CONTACT_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_report_contact_add)],
            WAIT_REPORT_CONTACT_DEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_report_contact_del)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True,
        per_chat=True,
    )
