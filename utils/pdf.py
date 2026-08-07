import pymupdf as fitz
from pathlib import Path


class PDFError(Exception):
    pass


def extract_text_from_pdf(file_path):
    path = Path(file_path)
    if not path.exists():
        raise PDFError("PDF file not found.")

    try:
        doc = fitz.open(str(path))
    except Exception:
        raise PDFError("Unable to open PDF file. The file may be corrupted.")

    text_parts = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        raise PDFError("No text could be extracted from this PDF. It may be image-based.")

    return full_text


def get_pdf_metadata(file_path):
    path = Path(file_path)
    try:
        doc = fitz.open(str(path))
        metadata = {
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
        }
        doc.close()
        return metadata
    except Exception:
        return {"page_count": 0, "title": "", "author": ""}


def summarize_pdf_prompts():
    return [
        "Summarize this PDF document",
        "Explain the main chapters",
        "Generate study notes from this PDF",
        "Create a quiz based on this PDF",
        "List the important questions from this PDF",
        "Translate the key points from this PDF",
    ]
