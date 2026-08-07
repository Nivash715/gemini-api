from flask import Blueprint, request, jsonify
from utils.database import (
    create_chat, delete_chat, get_all_chats, get_messages,
    get_chat, update_chat, clear_all_chats, add_message,
)
from utils.history import categorize_chats, get_chat_with_messages, search_chats
from utils.gemini import generate_chat_title

history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
def get_history():
    search = request.args.get("search", "").strip()
    chats = get_all_chats(search=search)
    categorized = categorize_chats(chats)
    return jsonify({"chats": categorized, "total": len(chats)})


@history_bp.route("/history/<int:chat_id>", methods=["GET"])
def get_single_chat(chat_id):
    result = get_chat_with_messages(chat_id)
    if not result:
        return jsonify({"error": "Chat not found."}), 404
    return jsonify(result)


@history_bp.route("/new-chat", methods=["POST"])
def new_chat():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "New Chat")
    chat_id = create_chat(title=title)
    return jsonify({"chat_id": chat_id, "title": title})


@history_bp.route("/delete-chat/<int:chat_id>", methods=["DELETE"])
def delete_single_chat(chat_id):
    chat = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404
    delete_chat(chat_id)
    return jsonify({"success": True, "message": "Chat deleted."})


@history_bp.route("/rename-chat/<int:chat_id>", methods=["PUT"])
def rename_chat(chat_id):
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title cannot be empty."}), 400

    chat = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404

    update_chat(chat_id, title=title[:100])
    return jsonify({"success": True, "title": title})


@history_bp.route("/pin-chat/<int:chat_id>", methods=["PUT"])
def pin_chat(chat_id):
    data = request.get_json(silent=True) or {}
    pinned = data.get("pinned", True)

    chat = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found."}), 404

    update_chat(chat_id, pinned=pinned)
    return jsonify({"success": True, "pinned": pinned})


@history_bp.route("/clear-history", methods=["DELETE"])
def clear_history():
    clear_all_chats()
    return jsonify({"success": True, "message": "All chat history cleared."})


@history_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
    results = search_chats(query)
    return jsonify({"results": results})
