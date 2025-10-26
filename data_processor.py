"""Data processing utilities for the Academic FAQ chatbot."""

import os
import re
from pathlib import Path
from typing import Dict, Iterator, List, Optional

import pdfplumber
import PyPDF2  # noqa: F401 - retained for potential future fallbacks
import pandas as pd  # noqa: F401 - reserved for future data handling
import requests
from bs4 import BeautifulSoup


class DocumentProcessor:
    """Extracts content from PDFs and web pages, then chunks the text."""

    def __init__(self):
        self.documents = []
        self.last_run_report: List[Dict[str, object]] = []

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
        self.last_run_report = []

        # Process PDFs
        pdf_dir_path = Path(pdf_dir)
        if pdf_dir_path.exists():
            for pdf_path in self._iter_pdf_files(pdf_dir_path):
                relative_path = pdf_path.relative_to(pdf_dir_path)
                display_name = relative_path.as_posix()
                print(f"Processing {display_name}...")

                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        total_chunks = 0
                        pages_processed = 0
                        for page_number, page in enumerate(pdf.pages, start=1):
                            table_text = []
                            for table in page.extract_tables() or []:
                                rows = [" | ".join(cell or "" for cell in row) for row in table]
                                table_text.append("\n".join(rows))

                            page_text = "\n".join(filter(None, [page.extract_text(), "\n\n".join(table_text)]))

                            if not page_text:
                                continue

                            pages_processed += 1
                            chunks = self.chunk_text(page_text)
                            total_chunks += len(chunks)
                            all_chunks.extend(
                                self._build_chunk_payload(
                                    chunks,
                                    source=f"{display_name} — page {page_number}",
                                    document_type="pdf",
                                    document_name=display_name,
                                    page=page_number,
                                    document_path=os.path.relpath(pdf_path, start=os.getcwd()),
                                )
                            )

                    self.last_run_report.append(
                        {
                            "path": display_name,
                            "document_type": "pdf",
                            "pages": pages_processed,
                            "chunks": total_chunks,
                            "bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
                        }
                    )
                    print(f"  Added {total_chunks} chunks across {pages_processed} pages")
                except Exception as exc:  # pragma: no cover - logging side-effect
                    print(f"Error processing {display_name}: {exc}")

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
                self.last_run_report.append(
                    {
                        "path": url,
                        "document_type": "url",
                        "pages": None,
                        "chunks": len(chunks),
                        "bytes": None,
                    }
                )
                print(f"  Added {len(chunks)} chunks")
        elif include_urls and urls_file:
            print(f"Warning: URLs file not found: {urls_file}")

        return all_chunks

    def _iter_pdf_files(self, root: Path) -> Iterator[Path]:
        """Yield PDF files recursively under the given root directory."""
        if not root.exists():
            return iter(())

        def generator() -> Iterator[Path]:
            for dirpath, _, filenames in os.walk(root):
                for filename in filenames:
                    if filename.lower().endswith(".pdf"):
                        yield Path(dirpath) / filename

        return generator()
