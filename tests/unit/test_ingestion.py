import io

from docx import Document

from creditflow.ingestion.chunking import fixed_size_chunks, recursive_chunks, semantic_chunks
from creditflow.ingestion.extractors import extract_document_text, validate_upload

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_docx_paragraph_and_table_extraction() -> None:
    document = Document()
    document.add_heading("Synthetic income statement")
    document.add_paragraph("Revenue and operating income are fictional.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "metric"
    table.cell(0, 1).text = "value"
    table.cell(1, 0).text = "revenue"
    table.cell(1, 1).text = "100000"
    buffer = io.BytesIO()
    document.save(buffer)
    content = buffer.getvalue()
    assert validate_upload("synthetic.docx", DOCX_MIME, content, 1_000_000)
    extracted = extract_document_text(content, DOCX_MIME)
    assert "Synthetic income statement" in extracted[0].text
    assert "revenue | 100000" in extracted[0].text


def test_all_three_chunking_strategies() -> None:
    assert len(fixed_size_chunks("a" * 30, size=10, overlap=2)) == 4
    assert recursive_chunks("first paragraph\n\nsecond paragraph", max_chars=18) == [
        "first paragraph",
        "second paragraph",
    ]
    vectors = {
        "Revenue increased.": [1.0, 0.0],
        "Sales improved.": [0.9, 0.1],
        "Debt rose.": [0.0, 1.0],
    }
    chunks = semantic_chunks(
        "Revenue increased. Sales improved. Debt rose.",
        vectors.__getitem__,
    )
    assert chunks == ["Revenue increased. Sales improved.", "Debt rose."]
