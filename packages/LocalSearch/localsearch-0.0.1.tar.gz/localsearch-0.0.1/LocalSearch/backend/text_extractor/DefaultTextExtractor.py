import os
from typing import List

import fitz
from bs4 import BeautifulSoup

from LocalSearch.backend.text_extractor.BaseTextExtractor import BaseTextExtractor


class DefaultTextExtractor(BaseTextExtractor):
    """
    Default text extractor supporting .txt, .pdf, and .html files.

    Provides optional text chunking with overlap for downstream processing.
    """

    SUPPORTED_TYPES = [".txt", ".pdf", ".html"]

    def __init__(self, base_path: str, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the default text extractor.

        Args:
            base_path: Base directory path for files.
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of characters to overlap between chunks.
        """
        self.base_path = base_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def can_handle(self, file_path: str) -> bool:
        """
        Check if the file extension is supported by this extractor.

        Args:
            file_path: Path to the file.

        Returns:
            True if the file type is supported, False otherwise.
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_TYPES

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks with optional overlap.

        Args:
            text: Full text to split.

        Returns:
            List of text chunks.
        """
        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap

        return chunks

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a supported file type.

        Args:
            file_path: Path to the file.

        Returns:
            Extracted text as a single string. Returns empty string on error.
        """
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".txt":
                return self._extract_txt(file_path)
            elif ext == ".pdf":
                return self._extract_pdf(file_path)
            elif ext == ".html":
                return self._extract_html(file_path)
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            print(f"[ERROR] Failed to extract text from {file_path}: {e}")
            return ""

    # --- Internal extraction methods ---

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from a .txt file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from a .pdf file using PyMuPDF (fitz)."""
        with fitz.open(file_path) as doc:
            text = "\n".join(page.get_text("text") for page in doc)
        return " ".join(text.split())

    def _extract_html(self, file_path: str) -> str:
        """Extract text from a .html file using BeautifulSoup."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)


