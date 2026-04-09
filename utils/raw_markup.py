"""
إرسال الأزرار بـ raw HTTP مباشرة للـ Bot API 9.4
يدعم: style (success/primary/danger) + icon_custom_emoji_id
"""
import json
import aiohttp
from telegram import Bot


async def _post(token: str, method: str, data: dict) -> dict:
    """
    نبعت reply_markup كـ JSON string منفصل عشان Telegram يقبله صح
    """
    url = f"https://api.telegram.org/bot{token}/{method}"
    # reply_markup لازم يكون string مش dict
    if "reply_markup" in data and isinstance(data["reply_markup"], dict):
        data = dict(data)
        data["reply_markup"] = json.dumps(data["reply_markup"], ensure_ascii=False)
    if "entities" in data and isinstance(data["entities"], list):
        data = dict(data)
        data["entities"] = json.dumps(data["entities"], ensure_ascii=False)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            result = await resp.json()
            return result


async def send_message_raw(
    bot: Bot,
    chat_id: int,
    text: str,
    rows: list[list[dict]],
    reply_to_message_id: int = None,
    entities: list = None,
) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": rows},
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    if entities:
        payload["entities"] = [
            {
                "type": e.type,
                "offset": e.offset,
                "length": e.length,
                **({"custom_emoji_id": e.custom_emoji_id} if e.custom_emoji_id else {})
            }
            for e in entities
        ]
    return await _post(bot.token, "sendMessage", payload)


async def edit_message_raw(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    rows: list[list[dict]],
) -> dict:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "reply_markup": {"inline_keyboard": rows},
    }
    return await _post(bot.token, "editMessageText", payload)
