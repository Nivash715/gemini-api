import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_VISION_MODEL, UTILITY_PROMPTS


class GeminiError(Exception):
    pass


def configure_gemini():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise GeminiError(
            "Invalid or missing Gemini API key. Please set GEMINI_API_KEY in your .env file."
        )
    genai.configure(api_key=GEMINI_API_KEY)


def get_generation_config(temperature=0.7, max_tokens=2048):
    return genai.types.GenerationConfig(
        temperature=float(temperature),
        max_output_tokens=int(max_tokens),
    )


def get_chat_model(temperature=0.7, max_tokens=2048):
    configure_gemini()
    return genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config=get_generation_config(temperature, max_tokens),
    )


def get_vision_model(temperature=0.7, max_tokens=2048):
    configure_gemini()
    return genai.GenerativeModel(
        GEMINI_VISION_MODEL,
        generation_config=get_generation_config(temperature, max_tokens),
    )


def build_history(messages):
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history


def generate_chat_response(messages, temperature=0.7, max_tokens=2048):
    try:
        model = get_chat_model(temperature, max_tokens)
        if len(messages) <= 1:
            response = model.generate_content(messages[-1]["content"])
        else:
            chat = model.start_chat(history=build_history(messages[:-1]))
            response = chat.send_message(messages[-1]["content"])
        return response.text
    except GeminiError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "invalid" in error_msg:
            raise GeminiError("Invalid API key. Please check your GEMINI_API_KEY.")
        if "network" in error_msg or "connection" in error_msg:
            raise GeminiError("No internet connection. Please check your network.")
        raise GeminiError(f"Gemini API error: {str(e)}")


def generate_stream(messages, temperature=0.7, max_tokens=2048):
    try:
        model = get_chat_model(temperature, max_tokens)
        if len(messages) <= 1:
            response = model.generate_content(
                messages[-1]["content"], stream=True
            )
        else:
            chat = model.start_chat(history=build_history(messages[:-1]))
            response = chat.send_message(messages[-1]["content"], stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text
    except GeminiError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg:
            raise GeminiError("Invalid API key. Please check your GEMINI_API_KEY.")
        if "network" in error_msg or "connection" in error_msg:
            raise GeminiError("No internet connection. Please check your network.")
        raise GeminiError(f"Gemini API error: {str(e)}")


def analyze_image(image_path, prompt, temperature=0.7, max_tokens=2048):
    try:
        import PIL.Image

        model = get_vision_model(temperature, max_tokens)
        image = PIL.Image.open(image_path)
        response = model.generate_content([prompt, image])
        return response.text
    except GeminiError:
        raise
    except Exception as e:
        raise GeminiError(f"Image analysis error: {str(e)}")


def analyze_document(text, prompt, temperature=0.7, max_tokens=2048):
    try:
        model = get_chat_model(temperature, max_tokens)
        full_prompt = (
            f"Based on the following document content, answer the user's question.\n\n"
            f"DOCUMENT:\n{text[:50000]}\n\n"
            f"USER QUESTION:\n{prompt}"
        )
        response = model.generate_content(full_prompt)
        return response.text
    except GeminiError:
        raise
    except Exception as e:
        raise GeminiError(f"Document analysis error: {str(e)}")


def run_utility(utility_type, content, temperature=0.7, max_tokens=2048):
    system_prompt = UTILITY_PROMPTS.get(utility_type)
    if not system_prompt:
        raise GeminiError(f"Unknown utility type: {utility_type}")

    try:
        model = get_chat_model(temperature, max_tokens)
        prompt = f"{system_prompt}\n\nInput:\n{content}"
        response = model.generate_content(prompt)
        return response.text
    except GeminiError:
        raise
    except Exception as e:
        raise GeminiError(f"Utility error: {str(e)}")


def generate_chat_title(first_message):
    try:
        model = get_chat_model(0.3, 50)
        prompt = (
            f"Generate a short title (max 6 words) for a chat that starts with: "
            f'"{first_message[:200]}". Return only the title, no quotes.'
        )
        response = model.generate_content(prompt)
        title = response.text.strip().strip('"').strip("'")
        return title[:60] if title else "New Chat"
    except Exception:
        return first_message[:40] + ("..." if len(first_message) > 40 else "")
