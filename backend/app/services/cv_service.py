"""CV upload: validation, text extraction, normalization, section detection.

Never executes uploaded files; only parses bytes.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import structlog

from app.core.config import settings
from app.core.constants import ALLOWED_CV_EXTENSIONS
from app.core.exceptions import UploadValidationError

logger = structlog.get_logger(__name__)

_MAGIC = {
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class ExtractedCV:
    text: str
    mime_type: str
    size_bytes: int
    content_hash: str
    sections: dict[str, str]


class CVService:
    def validate(self, *, filename: str, content: bytes) -> str:
        """Validate extension, magic bytes, and size. Returns detected mime."""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_CV_EXTENSIONS:
            raise UploadValidationError(
                f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_CV_EXTENSIONS)}"
            )
        max_bytes = settings.max_upload_size_bytes
        if len(content) > max_bytes:
            raise UploadValidationError(
                f"File exceeds maximum size of {settings.max_upload_size_mb} MB"
            )
        if not content:
            raise UploadValidationError("Empty file")
        mime = "text/plain"
        for magic, m in _MAGIC.items():
            if content.startswith(magic):
                mime = m
                break
        # Extension/mime consistency
        if ext == ".pdf" and mime != "application/pdf":
            raise UploadValidationError("File is not a valid PDF")
        if ext == ".docx" and not mime.endswith("wordprocessingml.document"):
            raise UploadValidationError("File is not a valid DOCX")
        return mime

    def extract_text(self, content: bytes, mime_type: str) -> str:
        try:
            if mime_type == "application/pdf":
                try:
                    import pymupdf as fitz_mod
                except ImportError:
                    import fitz as fitz_mod  # legacy alias
                with fitz_mod.open(stream=content, filetype="pdf") as doc:
                    return "\n".join(page.get_text() for page in doc)
            if mime_type.endswith("wordprocessingml.document"):
                import io

                import docx

                document = docx.Document(io.BytesIO(content))
                return "\n".join(p.text for p in document.paragraphs)
            return content.decode("utf-8", errors="replace")
        except Exception as exc:
            raise UploadValidationError(f"Failed to extract text: {exc}") from exc

    @staticmethod
    def normalize(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def detect_sections(text: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        current = "header"
        buf: list[str] = []
        for line in text.split("\n"):
            m = re.match(r"^([A-Z][A-Za-z /&+-]{2,60}):$", line.strip())
            if m:
                if buf:
                    sections[current] = "\n".join(buf).strip()
                current = m.group(1).strip().lower()
                buf = []
            else:
                buf.append(line)
        if buf:
            sections[current] = "\n".join(buf).strip()
        return sections

    def process_upload(self, *, filename: str, content: bytes) -> ExtractedCV:
        mime = self.validate(filename=filename, content=content)
        raw_text = self.extract_text(content, mime)
        normalized = self.normalize(raw_text)
        if len(normalized) < 40:
            raise UploadValidationError("Could not extract meaningful text from file")
        content_hash = hashlib.sha256(content).hexdigest()
        sections = self.detect_sections(normalized)
        logger.info(
            "cv.processed",
            filename=filename,
            chars=len(normalized),
            sections=len(sections),
        )
        return ExtractedCV(
            text=normalized,
            mime_type=mime,
            size_bytes=len(content),
            content_hash=content_hash,
            sections=sections,
        )
