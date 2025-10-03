"""Data processing utilities for the Academic FAQ chatbot."""

import os
import re
from typing import Dict, List, Optional

import pdfplumber
import PyPDF2  # noqa: F401 - retained for potential future fallbacks
import pandas as pd  # noqa: F401 - reserved for future data handling
import requests
from bs4 import BeautifulSoup


class DocumentProcessor:
    """Extracts content from PDFs and web pages, then chunks the text."""

    def __init__(self):
        self.documents = []

    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF using pdfplumber for better accuracy."""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as exc:  # pragma: no cover - logging side-effect
            print(f"Error extracting from {pdf_path}: {exc}")
        return text

    def extract_web_content(self, url):
        """Extract text from web pages."""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()

            text = soup.get_text()
            # Clean up text
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception as exc:  # pragma: no cover - logging side-effect
            print(f"Error extracting from {url}: {exc}")
            return ""

    def chunk_text(self, text, chunk_size=220, overlap=40):
        """Split text into overlapping chunks for better retrieval."""
        # Clean text first
        text = re.sub(r"\s+", " ", text.strip())

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if len(chunk.strip()) > 50:  # Only keep meaningful chunks
                chunks.append(chunk.strip())

        return chunks

    def _build_chunk_payload(
        self,
        chunks: List[str],
        *,
        source: str,
        document_type: str,
        document_name: str,
        page: Optional[int] = None,
        document_path: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """Attach metadata to raw text chunks."""

        payload: List[Dict[str, object]] = []
        for idx, chunk in enumerate(chunks, start=1):
            payload.append(
                {
                    "text": chunk,
                    "source": source,
                    "document_type": document_type,
                    "document_name": document_name,
                    "page": page,
                    "chunk_index": idx,
                    "document_path": document_path,
                }
            )
        return payload

    def process_all_documents(
        self,
        pdf_dir: str = "data/pdfs",
        urls_file: str = "data/urls.txt",
        include_urls: bool = True,
    ):
        """Process all PDFs and optional URLs into text chunks with metadata."""
        all_chunks: List[Dict[str, object]] = []

        # Process PDFs
        if os.path.exists(pdf_dir):
            for filename in os.listdir(pdf_dir):
                if not filename.lower().endswith(".pdf"):
                    continue

                pdf_path = os.path.join(pdf_dir, filename)
                print(f"Processing {filename}...")

                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        total_chunks = 0
                        for page_number, page in enumerate(pdf.pages, start=1):
                            page_text = page.extract_text()
                            if not page_text:
                                continue

                            chunks = self.chunk_text(page_text)
                            total_chunks += len(chunks)
                            all_chunks.extend(
                                self._build_chunk_payload(
                                    chunks,
                                    source=f"{filename} — page {page_number}",
                                    document_type="pdf",
                                    document_name=filename,
                                    page=page_number,
                                    document_path=os.path.relpath(pdf_path, start=os.getcwd()),
                                )
                            )

                        print(f"  Added {total_chunks} chunks")
                except Exception as exc:  # pragma: no cover - logging side-effect
                    print(f"Error processing {filename}: {exc}")

        # Process URLs
        if include_urls and urls_file and os.path.exists(urls_file):
            with open(urls_file, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file if line.strip() and not line.startswith("#")]

            for url in urls:
                print(f"Processing {url}...")
                text = self.extract_web_content(url)
                chunks = self.chunk_text(text)
                all_chunks.extend(
                    self._build_chunk_payload(
                        chunks,
                        source=url,
                        document_type="url",
                        document_name=url,
                        page=None,
                        document_path=url,
                    )
                )
                print(f"  Added {len(chunks)} chunks")
        elif include_urls and urls_file:
            print(f"⚠️  URLs file not found: {urls_file}")

        return all_chunks
