import io
import json
import zipfile
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT


def export_as_txt(chat_title, messages):
    lines = [f"Chat: {chat_title}", f"Exported: {datetime.utcnow().isoformat()}", "=" * 50, ""]
    for msg in messages:
        role = msg["role"].upper()
        timestamp = msg.get("created_at", "")
        lines.append(f"[{role}] {timestamp}")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines)


def export_as_markdown(chat_title, messages):
    lines = [f"# {chat_title}", f"*Exported: {datetime.utcnow().isoformat()}*", ""]
    for msg in messages:
        role = "**You**" if msg["role"] == "user" else "**Gemini**"
        lines.append(f"### {role}")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines)


def export_as_pdf(chat_title, messages):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ChatTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=12,
    )
    user_style = ParagraphStyle(
        "UserMsg",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20,
        textColor="#1a73e8",
    )
    ai_style = ParagraphStyle(
        "AIMsg",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=8,
        textColor="#666666",
    )

    story = []
    story.append(Paragraph(chat_title, title_style))
    story.append(Paragraph(f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", meta_style))
    story.append(Spacer(1, 0.3 * inch))

    for msg in messages:
        role = "You" if msg["role"] == "user" else "Gemini"
        timestamp = msg.get("created_at", "")[:19]
        story.append(Paragraph(f"{role} — {timestamp}", meta_style))

        content = msg["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = content.replace("\n", "<br/>")
        style = user_style if msg["role"] == "user" else ai_style
        story.append(Paragraph(content, style))
        story.append(Spacer(1, 0.15 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def export_as_docx(chat_title, messages):
    buffer = io.BytesIO()
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""

    body_parts = [
        f'<w:p><w:r><w:rPr><w:b/><w:sz w:val="36"/></w:rPr><w:t>{_escape_xml(chat_title)}</w:t></w:r></w:p>'
    ]

    for msg in messages:
        role = "You" if msg["role"] == "user" else "Gemini"
        timestamp = msg.get("created_at", "")[:19]
        body_parts.append(
            f'<w:p><w:r><w:rPr><w:i/><w:color w:val="666666"/></w:rPr>'
            f'<w:t>{_escape_xml(f"{role} — {timestamp}")}</w:t></w:r></w:p>'
        )
        for line in msg["content"].split("\n"):
            body_parts.append(
                f'<w:p><w:r><w:t>{_escape_xml(line)}</w:t></w:r></w:p>'
            )

    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
{"".join(body_parts)}
</w:body>
</w:document>"""

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)
        zf.writestr("word/document.xml", document)

    buffer.seek(0)
    return buffer.getvalue()


def export_chat(chat_title, messages, format_type):
    if format_type == "txt":
        return export_as_txt(chat_title, messages), "text/plain", "txt"
    elif format_type == "md" or format_type == "markdown":
        return export_as_markdown(chat_title, messages), "text/markdown", "md"
    elif format_type == "pdf":
        return export_as_pdf(chat_title, messages), "application/pdf", "pdf"
    elif format_type == "docx":
        return export_as_docx(chat_title, messages), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"
    elif format_type == "json":
        data = json.dumps({"title": chat_title, "messages": messages}, indent=2)
        return data, "application/json", "json"
    else:
        raise ValueError(f"Unsupported export format: {format_type}")


def _escape_xml(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
