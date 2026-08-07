import io
import uuid
from pathlib import Path
from PIL import Image
from config import UPLOAD_FOLDER, MAX_IMAGE_SIZE, ALLOWED_IMAGE_EXTENSIONS, IMAGE_TRANSFORM_PRESETS


class ImageError(Exception):
    pass


def validate_image(file):
    if not file or not file.filename:
        raise ImageError("No image file provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ImageError(
            f"Unsupported image format. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_IMAGE_SIZE:
        raise ImageError(f"Image too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)} MB.")

    return ext


def save_image(file):
    ext = validate_image(file)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_FOLDER / filename

    try:
        img = Image.open(file.stream)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(str(filepath), quality=95)
    except Exception:
        raise ImageError("Unable to process image file.")

    return filename, str(filepath)


def get_image_info(filepath):
    try:
        with Image.open(filepath) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
            }
    except Exception:
        return {}


def create_thumbnail(filepath, size=(200, 200)):
    try:
        with Image.open(filepath) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)
            return buffer
    except Exception:
        return None


class ImageTransformProvider:
    """
    Abstraction layer for image transformation.
    Currently uses Gemini vision for style analysis/description.
    Can be extended to connect image generation/editing APIs (DALL-E, Stable Diffusion, etc.)
    without changing the frontend.
    """

    def __init__(self, gemini_analyze_fn=None):
        self.gemini_analyze_fn = gemini_analyze_fn

    def transform(self, image_path, style_key, custom_prompt=None):
        preset = IMAGE_TRANSFORM_PRESETS.get(style_key, custom_prompt or "")
        if not preset and not custom_prompt:
            raise ImageError(f"Unknown transformation style: {style_key}")

        prompt = custom_prompt or preset

        if self.gemini_analyze_fn:
            result = self.gemini_analyze_fn(image_path, prompt)
            return {
                "status": "description",
                "message": result,
                "transformed_image": None,
                "style": style_key,
                "note": (
                    "Image transformation description generated. "
                    "Connect an image editing API to produce actual transformed images."
                ),
            }

        return {
            "status": "pending",
            "message": f"Transformation '{style_key}' queued for processing.",
            "transformed_image": None,
            "style": style_key,
        }

    def get_available_styles(self):
        return list(IMAGE_TRANSFORM_PRESETS.keys())


def get_transform_presets():
    return IMAGE_TRANSFORM_PRESETS
