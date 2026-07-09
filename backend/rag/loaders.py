"""AlgoQX Studio -- Document Loaders.

Loads documents from various file formats into plain text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_document(file_path: str) -> dict[str, Any]:
    """Load a document and extract text based on file type.

    Args:
        file_path: Path to the document file.

    Returns:
        Dictionary with keys: text, metadata, file_type
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    loaders = {
        ".pdf": _load_pdf,
        ".docx": _load_docx,
        ".txt": _load_text,
        ".md": _load_text,
        ".markdown": _load_text,
    }

    loader = loaders.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported file type: {ext}")

    text = loader(file_path)
    return {
        "text": text,
        "metadata": {
            "filename": path.name,
            "file_type": ext,
            "file_size": path.stat().st_size,
            "char_count": len(text),
        },
        "file_type": ext,
    }


def _load_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except Exception as e:
        raise RuntimeError(f"Failed to load PDF: {e}") from e


def _load_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise RuntimeError(f"Failed to load DOCX: {e}") from e


def _load_text(file_path: str) -> str:
    """Load a plain text or markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_website(url: str) -> dict[str, Any]:
    """Scrape text content from a website URL."""
    try:
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=30, headers={"User-Agent": "AlgoQX-Studio/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator="\n", strip=True)

        return {
            "text": text,
            "metadata": {
                "source": url,
                "file_type": "website",
                "char_count": len(text),
            },
            "file_type": "website",
        }
    except Exception as e:
        raise RuntimeError(f"Failed to load website: {e}") from e
