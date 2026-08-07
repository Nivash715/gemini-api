from datetime import datetime, timedelta
from utils.database import get_all_chats, get_messages, get_chat


def categorize_chats(chats):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)

    categories = {
        "pinned": [],
        "today": [],
        "yesterday": [],
        "last_week": [],
        "older": [],
    }

    for chat in chats:
        chat_dict = dict(chat)
        updated = datetime.fromisoformat(chat_dict["updated_at"])

        if chat_dict.get("pinned"):
            categories["pinned"].append(chat_dict)
        elif updated >= today_start:
            categories["today"].append(chat_dict)
        elif updated >= yesterday_start:
            categories["yesterday"].append(chat_dict)
        elif updated >= week_start:
            categories["last_week"].append(chat_dict)
        else:
            categories["older"].append(chat_dict)

    return categories


def get_chat_with_messages(chat_id):
    chat = get_chat(chat_id)
    if not chat:
        return None
    messages = get_messages(chat_id)
    return {
        "chat": dict(chat),
        "messages": messages,
    }


def format_messages_for_export(messages):
    formatted = []
    for msg in messages:
        formatted.append({
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg["created_at"],
        })
    return formatted


def search_chats(query, user_id=1):
    return [dict(c) for c in get_all_chats(user_id, search=query)]
