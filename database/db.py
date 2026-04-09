"""
قاعدة البيانات - JSON
"""
import json
import os
from config.settings import DATABASE_FILE, EMOJI

DEFAULT_DATA = {
    "admins": [],
    "middlemen": [],
    "super_middleman": None,
    "groups": {},
    "settings": {
        "auto_reply": True,
        **{f"emoji_{k}": v for k, v in EMOJI.items()},
    },
    "stats": {
        "total_replies": 0,
        "total_ton_requests": 0,
    }
}


def load_db() -> dict:
    if not os.path.exists(DATABASE_FILE):
        save_db(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key, val in DEFAULT_DATA.items():
        if key not in data:
            data[key] = val
    # تأكد من وجود كل مفاتيح الإيموجي
    for k, v in DEFAULT_DATA["settings"].items():
        if k not in data["settings"]:
            data["settings"][k] = v
    return data


def save_db(data: dict):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_emoji() -> dict:
    """جلب كل الإيموجي من الـ DB (قابلة للتعديل)"""
    s = load_db()["settings"]
    return {k: s.get(f"emoji_{k}", v) for k, v in EMOJI.items()}


# ─── Admins ───────────────────────────────────────────────
def add_admin(user_id: int):
    db = load_db()
    if user_id not in db["admins"]:
        db["admins"].append(user_id)
        save_db(db)

def remove_admin(user_id: int):
    db = load_db()
    db["admins"] = [a for a in db["admins"] if a != user_id]
    save_db(db)

def get_admins() -> list:
    return load_db()["admins"]

def is_admin(user_id: int) -> bool:
    return user_id in get_admins()


# ─── Middlemen ────────────────────────────────────────────
def add_middleman(name: str, username: str):
    db = load_db()
    entry = {"name": name, "username": username}
    if entry not in db["middlemen"]:
        db["middlemen"].append(entry)
        save_db(db)

def remove_middleman(username: str):
    db = load_db()
    db["middlemen"] = [m for m in db["middlemen"] if m["username"] != username]
    save_db(db)

def get_middlemen() -> list:
    return load_db()["middlemen"]

def set_super_middleman(name: str, username: str):
    db = load_db()
    db["super_middleman"] = {"name": name, "username": username}
    save_db(db)

def remove_super_middleman():
    db = load_db()
    db["super_middleman"] = None
    save_db(db)

def get_super_middleman():
    return load_db()["super_middleman"]


# ─── Groups ───────────────────────────────────────────────
def get_group_settings(chat_id: int) -> dict:
    db = load_db()
    return db["groups"].get(str(chat_id), {"auto_reply": True, "cooldown": {}})

def set_group_auto_reply(chat_id: int, enabled: bool):
    db = load_db()
    gid = str(chat_id)
    if gid not in db["groups"]:
        db["groups"][gid] = {"auto_reply": True, "cooldown": {}}
    db["groups"][gid]["auto_reply"] = enabled
    save_db(db)

def update_group_cooldown(chat_id: int, user_id: int, timestamp: float):
    db = load_db()
    gid = str(chat_id)
    if gid not in db["groups"]:
        db["groups"][gid] = {"auto_reply": True, "cooldown": {}}
    db["groups"][gid]["cooldown"][str(user_id)] = timestamp
    save_db(db)

def get_group_cooldown(chat_id: int, user_id: int) -> float:
    return load_db()["groups"].get(str(chat_id), {}).get("cooldown", {}).get(str(user_id), 0)


# ─── Settings ─────────────────────────────────────────────
def get_settings() -> dict:
    return load_db()["settings"]

def update_setting(key: str, value):
    db = load_db()
    db["settings"][key] = value
    save_db(db)

def is_auto_reply_enabled() -> bool:
    return load_db()["settings"].get("auto_reply", True)

def set_auto_reply(enabled: bool):
    update_setting("auto_reply", enabled)


# ─── Stats ────────────────────────────────────────────────
def increment_stat(key: str):
    db = load_db()
    db["stats"][key] = db["stats"].get(key, 0) + 1
    save_db(db)

def get_stats() -> dict:
    return load_db()["stats"]


# ─── جهات الإبلاغ ─────────────────────────────────────────
def get_report_contacts() -> list:
    return load_db().get("report_contacts", [])

def add_report_contact(username: str, label: str = ""):
    db = load_db()
    if "report_contacts" not in db:
        db["report_contacts"] = []
    username = username.lstrip("@")
    if not any(c["username"] == username for c in db["report_contacts"]):
        db["report_contacts"].append({"username": username, "label": label or username})
        save_db(db)
        return True
    return False

def remove_report_contact(username: str) -> bool:
    db = load_db()
    before = len(db.get("report_contacts", []))
    db["report_contacts"] = [c for c in db.get("report_contacts", []) if c["username"] != username.lstrip("@")]
    if len(db.get("report_contacts", [])) < before:
        save_db(db)
        return True
    return False
