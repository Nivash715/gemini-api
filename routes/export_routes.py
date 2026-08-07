from flask import Blueprint, request, jsonify, send_file
import io
import json

from utils.database import get_chat, get_messages, get_settings, update_setting, clear_all_chats
from utils.export import export_chat

export_bp = Blueprint("export", __name__)
settings_bp = Blueprint("settings", __name__)


@export_bp.route("/export/<int:chat_id>", methods=["GET"])
def export_single_chat(chat_id):
    format_type = request.args.get("format", "txt")
    chat = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404

    messages = get_messages(chat_id)
    if not messages:
        return jsonify({"error": "No messages to export."}), 400

    try:
        content, mime_type, ext = export_chat(dict(chat)["title"], messages, format_type)
        filename = f"{dict(chat)['title'][:30]}.{ext}".replace(" ", "_")

        return send_file(
            io.BytesIO(content if isinstance(content, bytes) else content.encode("utf-8")),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@export_bp.route("/import", methods=["POST"])
def import_chat():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "Imported Chat")
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages to import."}), 400

    from utils.database import create_chat, add_message

    chat_id = create_chat(title=title[:100])
    for msg in messages:
        add_message(chat_id, msg.get("role", "user"), msg.get("content", ""))

    return jsonify({"chat_id": chat_id, "title": title, "message_count": len(messages)})


@settings_bp.route("/settings", methods=["GET"])
def get_all_settings():
    settings = get_settings()
    return jsonify(settings)


@settings_bp.route("/settings", methods=["PUT"])
def update_settings():
    data = request.get_json(silent=True) or {}

    allowed_keys = {"theme", "temperature", "max_tokens", "voice_enabled", "auto_scroll"}
    updated = {}

    for key, value in data.items():
        if key in allowed_keys:
            update_setting(key, value)
            updated[key] = value

    return jsonify({"success": True, "updated": updated})


@settings_bp.route("/settings/clear-history", methods=["DELETE"])
def settings_clear_history():
    clear_all_chats()
    return jsonify({"success": True, "message": "History cleared."})
