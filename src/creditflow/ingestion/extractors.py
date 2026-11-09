import csv
import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from docx import Document as DocxDocument

SUPPORTED_TYPES = {
    "application/pdf",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class ExtractedPage:
    page: int
    text: str
    requires_ocr: bool = False


def validate_upload(filename: str, content_type: str, content: bytes, max_bytes: int) -> str:
    if not filename or Path(filename).name != filename:
        raise DocumentExtractionError("invalid filename")
    if content_type not in SUPPORTED_TYPES:
        raise DocumentExtractionError("unsupported media type")
    if not content or len(content) > max_bytes:
        raise DocumentExtractionError("file is empty or exceeds the configured size limit")
    if content_type == "application/pdf" and not content.startswith(b"%PDF"):
        raise DocumentExtractionError("content does not match declared PDF type")
    if content_type == "text/csv" and b"\x00" in content[:4096]:
        raise DocumentExtractionError("binary content is not valid CSV")
    if content_type.endswith("wordprocessingml.document") and not content.startswith(b"PK"):
        raise DocumentExtractionError("content does not match declared DOCX type")
    return hashlib.sha256(content).hexdigest()


def extract_document_text(content: bytes, content_type: str) -> list[ExtractedPage]:
    try:
        if content_type == "application/pdf":
            with pymupdf.open(stream=content, filetype="pdf") as document:  # type: ignore[no-untyped-call]
                return [
                    ExtractedPage(
                        page=i + 1,
                        text=page.get_text("text").strip(),
                        requires_ocr=not bool(page.get_text("text").strip()),
                    )
                    for i, page in enumerate(document)
                ]
        if content_type == "text/csv":
            rows = csv.reader(io.StringIO(content.decode("utf-8-sig")))
            return [
                ExtractedPage(
                    page=1, text="\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
                )
            ]
        if content_type.endswith("wordprocessingml.document"):
            document = DocxDocument(io.BytesIO(content))
            blocks = [
                paragraph.text.strip()
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]
            for table_index, table in enumerate(document.tables, start=1):
                blocks.append(f"[TABLE {table_index}]")
                blocks.extend(
                    " | ".join(cell.text.strip() for cell in row.cells) for row in table.rows
                )
            return [ExtractedPage(page=1, text="\n\n".join(blocks))]
    except (ValueError, UnicodeDecodeError, pymupdf.FileDataError, OSError) as exc:
        raise DocumentExtractionError("document extraction failed") from exc
    raise DocumentExtractionError("XLSX requires the optional openpyxl ingestion adapter")


def identify_document_type(text: str) -> str:
    lowered = text.lower()
    markers = {
        "balance_sheet": ("assets", "liabilities", "equity"),
        "income_statement": ("revenue", "operating income", "net income"),
        "cash_flow_statement": ("cash flow", "operating activities"),
        "loan_application": ("requested amount", "borrower"),
        "collateral_schedule": ("collateral", "appraised value"),
    }
    scores = {
        kind: sum(marker in lowered for marker in required) for kind, required in markers.items()
    }
    best = max(scores, key=lambda name: scores[name])
    return best if scores[best] else "unknown"


def validate_document_completeness(pages: list[ExtractedPage]) -> list[str]:
    if not pages:
        return ["NO_PAGES"]
    issues = ["OCR_REQUIRED"] if any(page.requires_ocr for page in pages) else []
    mentions = [
        int(value) for page in pages for value in re.findall(r"Page\s+(\d+)", page.text, re.I)
    ]
    if mentions and sorted(set(mentions)) != list(range(min(mentions), max(mentions) + 1)):
        issues.append("POSSIBLE_MISSING_PAGES")
    return issues


def chunk_document(
    document_id: str, pages: list[ExtractedPage], *, max_chars: int = 1200
) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    for page in pages:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", page.text) if part.strip()]
        current = ""
        for paragraph in paragraphs:
            if current and len(current) + len(paragraph) + 2 > max_chars:
                chunks.append(_chunk(document_id, page.page, len(chunks), current))
                current = ""
            current = f"{current}\n\n{paragraph}".strip()
        if current:
            chunks.append(_chunk(document_id, page.page, len(chunks), current))
    return chunks


def _chunk(document_id: str, page: int, index: int, text: str) -> dict[str, object]:
    return {
        "citation_id": f"{document_id}:p{page}:c{index}",
        "page": page,
        "index": index,
        "text": text,
        "content_hash": hashlib.sha256(text.encode()).hexdigest(),
    }
