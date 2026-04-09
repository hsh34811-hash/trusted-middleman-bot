"""
أدوات مساعدة - أزرار Bot API 9.4 + Custom Emoji
كل إيموجي في مكانه المحدد — لا تكرار
"""
from telegram import MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
from database.db import get_emoji


def ce(offset: int, length: int, emoji_id: str) -> MessageEntity:
    return MessageEntity(type="custom_emoji", offset=offset, length=length, custom_emoji_id=emoji_id)


def _utf16_len(text: str) -> int:
    """حساب طول النص بوحدات UTF-16 (الطريقة الصح لـ Telegram)"""
    return len(text.encode("utf-16-le")) // 2


def btn(text: str, callback: str = None, url: str = None,
        style: str = None, emoji_id: str = None) -> InlineKeyboardButton:
    extra = {}
    if style:
        extra["style"] = style
    if emoji_id:
        extra["icon_custom_emoji_id"] = emoji_id
    return InlineKeyboardButton(
        text=text, callback_data=callback, url=url,
        api_kwargs=extra or None,
    )


# ─── /start ───────────────────────────────────────────────
def build_start_message(first_name: str) -> tuple[str, list[MessageEntity]]:
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("👋", e["wave"])
    add(f" أهلاً {first_name}!\n\n")
    add("🛡", e["shield"])
    add(" أنا بوت الوسيط الموثوق\n")
    add("أحمي المستخدمين من النصب في المجموعات.\n\n")
    add("اختر من القائمة أدناه:")
    return "".join(parts), entities


def build_start_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    from config.settings import OWNER_ID
    from database.db import is_admin
    e = get_emoji()
    rows = [
        [
            btn("قائمة الوسطاء",  "list_middlemen",  style="primary", emoji_id=e["btn_list"]),
            btn("الوسيط الأعلى",  "super_middleman", style="primary", emoji_id=e["btn_super"]),
        ],
        [
            btn("سعر TON",        "start_ton",       style="success", emoji_id=e["btn_ton"]),
            btn("تحويل العملات",  "start_convert",   style="success", emoji_id=e["btn_convert"]),
        ],
        [
            btn("القواعد",        "rules",           style="success", emoji_id=e["btn_rules"]),
            btn("تحقق من وسيط",  "start_verify",    style="primary", emoji_id=e["search"]),
        ],
        [
            btn("بلغ عن نصاب",   "report_scam",     style="danger",  emoji_id=e["btn_scam"]),
            btn("قائمة النصابين","show_blacklist",   style="danger",  emoji_id=e["banned"]),
        ],
    ]
    if user_id and (user_id == OWNER_ID or is_admin(user_id)):
        rows.append([btn("لوحة التحكم", "open_panel", style="primary", emoji_id=e["btn_panel"])])
    return InlineKeyboardMarkup(rows)


# ─── رسالة الوسيط في المجموعة ─────────────────────────────
def build_middleman_message(middlemen: list, super_middleman: dict | None) -> tuple[str, list[MessageEntity]]:
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("⚠️", e["warn"])
    add(" تحذير هام — بوت الوسيط الموثوق ")
    add("⚠️", e["warn"])
    add("\n\n")
    add("🛡", e["shield"])
    add(" قبل أي صفقة تأكد من التعامل مع وسيط موثوق فقط!\n\n")
    add("✅", e["check"])
    add(" الوسطاء الموثوقون:\n")
    for m in middlemen:
        add("💥", e["verified"])
        add(f" {m['name']} — @{m['username']}\n")

    if super_middleman:
        add("\n")
        add("⭐", e["star"])
        add(f" الوسيط الأعلى موثوقية:\n")
        add("👑", e["btn_crown"])
        add(f" {super_middleman['name']} — @{super_middleman['username']}\n")

    add("\n")
    add("✍️", e["pen"])
    add(" القواعد:\n")
    add("1⃣", e["num_1"]); add(" لا تحول أموال بدون وسيط\n")
    add("2⃣", e["num_2"]); add(" تأكد من هوية الوسيط\n")
    add("3⃣", e["num_3"]); add(" احتفظ بسجل المحادثة\n")
    add("4⃣", e["num_4"]); add(" لا تشارك بياناتك الشخصية\n")
    return "".join(parts), entities


def build_middleman_keyboard() -> InlineKeyboardMarkup:
    e = get_emoji()
    return InlineKeyboardMarkup([
        [btn("الوسيط الأعلى موثوقية", "super_middleman",   style="primary", emoji_id=e["btn_super"])],
        [btn("القواعد",               "rules",             style="success", emoji_id=e["btn_rules"])],
        [btn("تحقق من وسيط",         "start_verify",      style="primary", emoji_id=e["search"])],
        [btn("تواصل مع الوسيط",      "contact_middleman", style="success", emoji_id=e["btn_contact"])],
        [btn("بلغ عن نصاب",          "report_scam",       style="danger",  emoji_id=e["btn_scam"])],
    ])


# ─── رسالة الوسيط الأعلى ─────────────────────────────────
def build_super_middleman_message(super_m: dict) -> tuple[str, list[MessageEntity]]:
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("⭐", e["star"])
    add(" الوسيط الأعلى موثوقية:\n\n")
    add("👑", e["btn_crown"])
    add(f" {super_m['name']} — @{super_m['username']}")
    return "".join(parts), entities


# ─── رسالة القواعد ────────────────────────────────────────
def build_rules_message() -> tuple[str, list[MessageEntity]]:
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("✍️", e["pen"])
    add(" القواعد:\n\n")
    add("1⃣", e["num_1"]); add(" لا تحول أموال بدون وسيط\n")
    add("2⃣", e["num_2"]); add(" تأكد من هوية الوسيط\n")
    add("3⃣", e["num_3"]); add(" احتفظ بسجل المحادثة\n")
    add("4⃣", e["num_4"]); add(" لا تشارك بياناتك الشخصية")
    return "".join(parts), entities


# ─── رسالة تواصل مع الوسيط ───────────────────────────────
def build_contact_message(middlemen: list) -> tuple[str, list[MessageEntity]]:
    e = get_emoji()
    entities, parts, cur = [], [], 0

    def add(text: str, eid: str = None):
        nonlocal cur
        if eid:
            entities.append(ce(cur, _utf16_len(text), eid))
        parts.append(text)
        cur += _utf16_len(text)

    add("✅", e["check"])
    add(" تواصل مع أحد الوسطاء الموثوقين:\n\n")
    for m in middlemen:
        add("💥", e["verified"])
        add(f" {m['name']} — @{m['username']}\n")
    return "".join(parts), entities


# ─── Report keyboard ─────────────────────────────────────
def build_report_keyboard() -> InlineKeyboardMarkup | None:
    from database.db import get_report_contacts
    e = get_emoji()
    contacts = get_report_contacts()
    if not contacts:
        return None
    rows = []
    for c in contacts:
        rows.append([btn(f"تواصل مع {c['label']}", url=f"https://t.me/{c['username']}", style="danger", emoji_id=e["btn_scam"])])
    return InlineKeyboardMarkup(rows)


# ─── Rating keyboard ──────────────────────────────────────
def build_rating_keyboard(username: str) -> InlineKeyboardMarkup:
    e = get_emoji()
    # كل صف فيه زر واحد — النجوم بـ custom emoji بعدد الرقم
    rows = []
    labels = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}
    styles = {1: "danger", 2: "danger", 3: "primary", 4: "success", 5: "success"}
    for n in range(1, 6):
        rows.append([btn(labels[n], f"rate_{username}_{n}", style=styles[n], emoji_id=e["rating"])])
    return InlineKeyboardMarkup(rows)


# ─── TON ──────────────────────────────────────────────────
def build_ton_keyboard() -> InlineKeyboardMarkup:
    e = get_emoji()
    return InlineKeyboardMarkup([
        [
            btn("تحديث السعر", "refresh_ton", style="primary", emoji_id=e["btn_refresh"]),
            btn("CoinGecko", url="https://www.coingecko.com/en/coins/toncoin", style="success"),
        ],
    ])


# ─── Owner panel ──────────────────────────────────────────
def build_owner_panel_keyboard() -> InlineKeyboardMarkup:
    e = get_emoji()
    return InlineKeyboardMarkup([
        [
            btn("إضافة أدمن",          "owner_add_admin",        style="success", emoji_id=e["btn_add"]),
            btn("حذف أدمن",            "owner_remove_admin",     style="danger",  emoji_id=e["btn_remove"]),
        ],
        [
            btn("إضافة وسيط",          "owner_add_middleman",    style="success", emoji_id=e["btn_add"]),
            btn("حذف وسيط",            "owner_remove_middleman", style="danger",  emoji_id=e["btn_remove"]),
        ],
        [
            btn("تعيين وسيط أعلى",     "owner_set_super",        style="primary", emoji_id=e["btn_crown"]),
            btn("حذف وسيط أعلى",       "owner_remove_super",     style="danger",  emoji_id=e["btn_remove"]),
        ],
        [
            btn("تفعيل الرد التلقائي", "owner_enable_reply",     style="success", emoji_id=e["btn_enable"]),
            btn("إيقاف الرد التلقائي", "owner_disable_reply",    style="danger",  emoji_id=e["btn_disable"]),
        ],
        [
            btn("إضافة نصاب",          "owner_add_blacklist",       style="danger",  emoji_id=e["add_ban"]),
            btn("حذف من القائمة",      "owner_del_blacklist",       style="danger",  emoji_id=e["del_ban"]),
        ],
        [
            btn("جهات الإبلاغ +",      "owner_add_report_contact",  style="success", emoji_id=e["btn_add"]),
            btn("جهات الإبلاغ -",      "owner_del_report_contact",  style="danger",  emoji_id=e["btn_remove"]),
        ],
        [
            btn("تعديل الإيموجي",      "owner_edit_emoji",       style="primary", emoji_id=e["btn_edit"]),
            btn("سعر TON",             "owner_ton",              style="primary", emoji_id=e["btn_ton"]),
        ],
        [
            btn("الإحصائيات",          "owner_stats",            style="primary", emoji_id=e["btn_stats"]),
            btn("سجل العمليات",        "owner_logs",             style="primary", emoji_id=e["log"]),
        ],
        [
            btn("المجموعات",           "owner_groups",           style="primary", emoji_id=e["btn_groups"]),
            btn("رجوع",                "owner_back",             style="danger",  emoji_id=e["btn_back"]),
        ],
    ])


# ─── Admin panel ──────────────────────────────────────────
def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    e = get_emoji()
    return InlineKeyboardMarkup([
        [
            btn("إضافة وسيط",  "admin_add_middleman",    style="success", emoji_id=e["btn_add"]),
            btn("حذف وسيط",    "admin_remove_middleman", style="danger",  emoji_id=e["btn_remove"]),
        ],
        [
            btn("عرض القائمة", "admin_list",             style="primary", emoji_id=e["btn_list"]),
        ],
        [
            btn("رجوع",        "admin_back",             style="danger",  emoji_id=e["btn_back"]),
        ],
    ])
