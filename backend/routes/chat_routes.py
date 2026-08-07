import os
import uuid
import bleach
from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER, MAX_PDF_SIZE, ALLOWED_PDF_EXTENSIONS
from utils.database import (
    create_chat, add_message, get_messages, get_chat, update_chat,
    get_settings, get_pdf_documents, save_pdf_document, delete_last_assistant_message,
)
from utils.gemini import (
    generate_chat_response, generate_stream, analyze_image,
    analyze_document, run_utility, generate_chat_title, GeminiError,
)
from utils.image import save_image, ImageTransformProvider, ImageError
from utils.pdf import extract_text_from_pdf, PDFError

chat_bp = Blueprint("chat", __name__)

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "th", "td", "a", "span",
]


def sanitize(text):
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = sanitize(data.get("message", "").strip())
    chat_id = data.get("chat_id")
    stream = data.get("stream", True)
    utility = data.get("utility")

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    settings = get_settings()
    temperature = float(settings.get("temperature", 0.7))
    max_tokens = int(settings.get("max_tokens", 2048))

    if not chat_id:
        chat_id = create_chat()
        update_chat(chat_id, title=generate_chat_title(message))

    add_message(chat_id, "user", message)

    history = get_messages(chat_id)
    api_messages = [{"role": m["role"], "content": m["content"]} for m in history]

    pdf_docs = get_pdf_documents(chat_id)
    if pdf_docs and not utility:
        doc_text = pdf_docs[0]["extracted_text"]
        try:
            if stream:
                def generate():
                    full_response = ""
                    try:
                        response = analyze_document(doc_text, message, temperature, max_tokens)
                        for i in range(0, len(response), 3):
                            chunk = response[i:i + 3]
                            full_response += chunk
                            yield f"data: {chunk}\n\n"
                        add_message(chat_id, "assistant", full_response)
                        yield f"data: [DONE:{chat_id}]\n\n"
                    except GeminiError as e:
                        yield f"data: [ERROR:{str(e)}]\n\n"

                return Response(
                    stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
                )
            else:
                response = analyze_document(doc_text, message, temperature, max_tokens)
                add_message(chat_id, "assistant", response)
                return jsonify({"response": response, "chat_id": chat_id})
        except GeminiError as e:
            return jsonify({"error": str(e)}), 500

    try:
        if utility:
            response = run_utility(utility, message, temperature, max_tokens)
            add_message(chat_id, "assistant", response)
            return jsonify({"response": response, "chat_id": chat_id})

        if stream:
            def generate():
                full_response = ""
                try:
                    for chunk in generate_stream(api_messages, temperature, max_tokens):
                        full_response += chunk
                        yield f"data: {chunk}\n\n"
                    add_message(chat_id, "assistant", full_response)
                    yield f"data: [DONE:{chat_id}]\n\n"
                except GeminiError as e:
                    yield f"data: [ERROR:{str(e)}]\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        else:
            response = generate_chat_response(api_messages, temperature, max_tokens)
            add_message(chat_id, "assistant", response)
            return jsonify({"response": response, "chat_id": chat_id})

    except GeminiError as e:
        return jsonify({"error": str(e)}), 500
    except Exception:
        return jsonify({"error": "An unexpected server error occurred."}), 500


@chat_bp.route("/chat/regenerate", methods=["POST"])
def regenerate():
    data = request.get_json(silent=True) or {}
    chat_id = data.get("chat_id")

    if not chat_id:
        return jsonify({"error": "Chat ID required."}), 400

    messages = get_messages(chat_id)
    if len(messages) < 2:
        return jsonify({"error": "No message to regenerate."}), 400

    delete_last_assistant_message(chat_id)
    messages = get_messages(chat_id)

    if not messages or messages[-1]["role"] != "user":
        return jsonify({"error": "No user message found."}), 400

    settings = get_settings()
    temperature = float(settings.get("temperature", 0.7))
    max_tokens = int(settings.get("max_tokens", 2048))
    api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    def generate():
        full_response = ""
        try:
            for chunk in generate_stream(api_messages, temperature, max_tokens):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            add_message(chat_id, "assistant", full_response)
            yield f"data: [DONE:{chat_id}]\n\n"
        except GeminiError as e:
            yield f"data: [ERROR:{str(e)}]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chat_bp.route("/upload-image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    chat_id = request.form.get("chat_id")
    prompt = sanitize(request.form.get("prompt", "Describe this image in detail."))
    mode = request.form.get("mode", "analyze")
    style = request.form.get("style", "")

    try:
        filename, filepath = save_image(file)

        if not chat_id:
            chat_id = create_chat(title="Image Chat")

        settings = get_settings()
        temperature = float(settings.get("temperature", 0.7))
        max_tokens = int(settings.get("max_tokens", 2048))

        if mode == "transform":
            provider = ImageTransformProvider(gemini_analyze_fn=analyze_image)
            result = provider.transform(filepath, style, custom_prompt=prompt)
            response_text = result["message"]
            if result.get("note"):
                response_text += f"\n\n*{result['note']}*"
        else:
            response_text = analyze_image(filepath, prompt, temperature, max_tokens)

        add_message(
            chat_id, "user", prompt,
            attachments=[{"type": "image", "filename": filename}],
        )
        add_message(chat_id, "assistant", response_text)

        return jsonify({
            "response": response_text,
            "chat_id": chat_id,
            "filename": filename,
            "image_url": f"/uploads/{filename}",
        })

    except (ImageError, GeminiError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Failed to process image."}), 500


@chat_bp.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    chat_id = request.form.get("chat_id")

    if not file.filename:
        return jsonify({"error": "No file selected."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_PDF_EXTENSIONS:
        return jsonify({"error": "Only PDF files are supported."}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_PDF_SIZE:
        return jsonify({"error": f"PDF too large. Max size: {MAX_PDF_SIZE // (1024*1024)} MB."}), 400

    try:
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        safe_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        filepath = UPLOAD_FOLDER / unique_name
        file.save(str(filepath))

        extracted_text = extract_text_from_pdf(str(filepath))

        if not chat_id:
            chat_id = create_chat(title=f"PDF: {safe_name[:30]}")

        save_pdf_document(chat_id, safe_name, extracted_text)
        update_chat(chat_id, title=f"PDF: {safe_name[:30]}")

        word_count = len(extracted_text.split())
        preview = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")

        welcome_msg = (
            f"PDF **{safe_name}** uploaded successfully!\n\n"
            f"- Pages processed\n"
            f"- ~{word_count} words extracted\n\n"
            f"**Preview:**\n{preview}\n\n"
            f"You can now ask questions about this document."
        )
        add_message(chat_id, "assistant", welcome_msg)

        return jsonify({
            "chat_id": chat_id,
            "filename": safe_name,
            "word_count": word_count,
            "preview": preview,
            "message": welcome_msg,
        })

    except PDFError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Failed to process PDF."}), 500


@chat_bp.route("/voice", methods=["POST"])
def voice_chat():
    data = request.get_json(silent=True) or {}
    text = sanitize(data.get("text", "").strip())
    chat_id = data.get("chat_id")

    if not text:
        return jsonify({"error": "No speech text provided."}), 400

    settings = get_settings()
    temperature = float(settings.get("temperature", 0.7))
    max_tokens = int(settings.get("max_tokens", 2048))

    if not chat_id:
        chat_id = create_chat(title=generate_chat_title(text))

    add_message(chat_id, "user", text)

    try:
        history = get_messages(chat_id)
        api_messages = [{"role": m["role"], "content": m["content"]} for m in history]
        response = generate_chat_response(api_messages, temperature, max_tokens)
        add_message(chat_id, "assistant", response)
        return jsonify({"response": response, "chat_id": chat_id})
    except GeminiError as e:
        return jsonify({"error": str(e)}), 500
