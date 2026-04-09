"""
نظام الـ Cooldown لمنع السبام
"""
import time
from database.db import get_group_cooldown, update_group_cooldown
from config.settings import COOLDOWN_SECONDS


def is_on_cooldown(chat_id: int, user_id: int) -> bool:
    """هل المستخدم في فترة الـ cooldown؟"""
    last_time = get_group_cooldown(chat_id, user_id)
    return (time.time() - last_time) < COOLDOWN_SECONDS


def set_cooldown(chat_id: int, user_id: int):
    """تسجيل وقت آخر رد"""
    update_group_cooldown(chat_id, user_id, time.time())
