import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv("SECRET_KEY", "gemini-ai-assistant-secret-key-change-in-production")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash")

DATABASE_PATH = BASE_DIR / "database" / "chat.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
STATIC_IMAGES = BASE_DIR / "static" / "images"

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_PDF_EXTENSIONS = {"pdf"}

DEFAULT_SETTINGS = {
    "theme": "dark",
    "temperature": "0.7",
    "max_tokens": "2048",
    "voice_enabled": "true",
    "auto_scroll": "true",
}

# Image transformation styles (extensible for future API integration)
IMAGE_TRANSFORM_PRESETS = {
    "anime": "Convert this image into anime style artwork with vibrant colors and clean lines.",
    "ghibli": "Transform this image into Studio Ghibli animation style with soft watercolor aesthetics.",
    "pixar": "Convert this image into Pixar 3D animation style with smooth rendering.",
    "remove_background": "Remove the background from this image, keeping only the main subject.",
    "replace_background": "Replace the background with a professional studio backdrop.",
    "black_white": "Convert this image to a high-contrast black and white photograph.",
    "sketch": "Convert this image into a detailed pencil sketch drawing.",
    "oil_painting": "Transform this image into an oil painting with rich textures.",
    "watercolor": "Convert this image into a soft watercolor painting.",
    "cartoon": "Convert this image into a colorful cartoon illustration.",
    "portrait": "Enhance this into a professional portrait with studio lighting.",
    "enhance": "Enhance the quality, sharpness, and clarity of this image.",
    "upscale": "Upscale and enhance the resolution and detail of this image.",
    "restore": "Restore and repair this old or damaged photo.",
}

UTILITY_PROMPTS = {
    "grammar": "You are a grammar checker. Fix grammar, spelling, and punctuation. Return the corrected text with brief explanations.",
    "resume": "You are a resume analyzer. Analyze this resume and provide strengths, weaknesses, and improvement suggestions.",
    "cover_letter": "You are a cover letter generator. Write a professional cover letter based on the provided information.",
    "email": "You are an email generator. Write a professional email based on the provided context.",
    "blog": "You are a blog writer. Write an engaging, SEO-friendly blog post on the given topic.",
    "code": "You are a code generator. Write clean, well-documented code for the given requirements.",
    "sql": "You are a SQL generator. Write optimized SQL queries for the given requirements.",
    "regex": "You are a regex generator. Create and explain regex patterns for the given requirements.",
    "json": "You are a JSON formatter. Format, validate, and explain the given JSON data.",
    "translate": "You are a translator. Translate the given text accurately while preserving meaning and tone.",
    "summarize": "You are a summarizer. Provide a concise, comprehensive summary of the given text.",
}
