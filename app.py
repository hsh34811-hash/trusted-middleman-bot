"""
البوت الرئيسي - Trusted Middleman Bot
python-telegram-bot v21+
"""
import logging
import warnings
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
)
from config.settings import BOT_TOKEN
from handlers.admin import (
    start_command, panel_command, middlemen_command, ton_command, stats_command,
    owner_callback_handler, owner_simple_callback_handler,
    build_conversation_handler,
    receive_admin_id, receive_remove_admin_id,
    receive_middleman_name, receive_middleman_username,
    receive_remove_middleman, receive_super_name, receive_super_username,
    receive_emoji_value, receive_blacklist_add, receive_blacklist_del,
    receive_report_contact_add, receive_report_contact_del,
    cancel_conversation,
    WAIT_ADMIN_ID, WAIT_REMOVE_ADMIN_ID,
    WAIT_MIDDLEMAN_NAME, WAIT_MIDDLEMAN_USERNAME,
    WAIT_REMOVE_MIDDLEMAN, WAIT_SUPER_NAME, WAIT_SUPER_USERNAME,
    WAIT_EMOJI_KEY, WAIT_BLACKLIST_ADD, WAIT_BLACKLIST_DEL,
    WAIT_REPORT_CONTACT_ADD, WAIT_REPORT_CONTACT_DEL,
)
from handlers.group import (
    group_message_handler,
    middleman_list_callback,
    super_middleman_callback,
    rules_callback,
    report_scam_callback,
    contact_middleman_callback,
    start_ton_callback,
    open_panel_callback,
    back_callback,
    verify_callback,
    blacklist_callback,
    rate_callback,
)
from handlers.ton_price import ton_price_handler, ton_refresh_callback
from handlers.features import check_price_alerts

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)

# أزرار تبدأ conversation
CONV_PATTERN = (
    "^(owner_add_admin|owner_remove_admin|owner_add_middleman|owner_remove_middleman"
    "|owner_set_super|owner_edit_emoji|admin_add_middleman|admin_remove_middleman"
    "|owner_add_blacklist|owner_del_blacklist"
    "|owner_add_report_contact|owner_del_report_contact)$"
)

# أزرار فورية
SIMPLE_PATTERN = (
    "^(owner_enable_reply|owner_disable_reply|owner_ton|owner_stats|owner_groups"
    "|owner_back|admin_back|admin_list|owner_logs|owner_remove_super)$"
)


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # ─── أوامر أساسية ─────────────────────────────────────
    app.add_handler(CommandHandler("start",      start_command))
    app.add_handler(CommandHandler("panel",      panel_command))
    app.add_handler(CommandHandler("middlemen",  middlemen_command))
    app.add_handler(CommandHandler("ton",        ton_command))
    app.add_handler(CommandHandler("verify",     verify_callback))
    app.add_handler(CommandHandler("stats",      stats_command))

    # ─── ConversationHandler ──────────────────────────────
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(owner_callback_handler, pattern=CONV_PATTERN),
        ],
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
        per_message=False,
        allow_reentry=True,
    )
    app.add_handler(conv)

    # ─── Callbacks فورية للوحة التحكم ─────────────────────
    app.add_handler(CallbackQueryHandler(owner_simple_callback_handler, pattern=SIMPLE_PATTERN))

    # ─── Callbacks للمجموعات والميزات ─────────────────────
    app.add_handler(CallbackQueryHandler(middleman_list_callback,    pattern="^list_middlemen$"))
    app.add_handler(CallbackQueryHandler(super_middleman_callback,   pattern="^super_middleman$"))
    app.add_handler(CallbackQueryHandler(rules_callback,             pattern="^rules$"))
    app.add_handler(CallbackQueryHandler(report_scam_callback,       pattern="^report_scam$"))
    app.add_handler(CallbackQueryHandler(contact_middleman_callback, pattern="^contact_middleman$"))
    app.add_handler(CallbackQueryHandler(start_ton_callback,         pattern="^start_ton$"))
    app.add_handler(CallbackQueryHandler(open_panel_callback,        pattern="^open_panel$"))
    app.add_handler(CallbackQueryHandler(back_callback,              pattern="^back$"))
    app.add_handler(CallbackQueryHandler(verify_callback,            pattern="^start_verify$"))
    app.add_handler(CallbackQueryHandler(blacklist_callback,         pattern="^show_blacklist$"))
    app.add_handler(CallbackQueryHandler(rate_callback,              pattern=r"^rate_\w+_[1-5]$"))

    # ─── Callback تحديث سعر TON ───────────────────────────
    app.add_handler(CallbackQueryHandler(ton_refresh_callback, pattern="^refresh_ton$"))

    # ─── تحويل العملات في الخاص ───────────────────────────
    app.add_handler(CallbackQueryHandler(
        lambda u, c: start_convert_callback(u, c), pattern="^start_convert$"
    ))

    # ─── رسائل المجموعات ──────────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        group_message_handler
    ))

    # ─── رسائل الخاص ──────────────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        ton_price_handler
    ))

    # ─── تنبيهات السعر كل دقيقة ───────────────────────────
    if app.job_queue:
        app.job_queue.run_repeating(check_price_alerts, interval=60, first=10)
    else:
        logger.warning("job_queue غير متاح — تنبيهات السعر معطلة")

    return app


async def start_convert_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "💱 أرسل المبلغ والعملة للتحويل:\n\n"
        "مثال:\n"
        "• 10 ton\n"
        "• 100 دولار\n"
        "• 500 جنيه"
    )


if __name__ == "__main__":
    logger.info("🚀 بدء تشغيل البوت...")
    app = build_app()
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
