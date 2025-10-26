"""Semantic search utilities for the Academic FAQ chatbot."""

import os
import pickle
import re
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

import faiss
import numpy as np

import huggingface_hub  # type: ignore
from huggingface_hub import hf_hub_download

try:  # pragma: no cover - optional dependency is exercised indirectly
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv may be absent at runtime
    load_dotenv = None  # type: ignore

if load_dotenv is not None:  # pragma: no cover - simple configuration helper
    load_dotenv()

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "about",
    "at",
    "be",
    "but",
    "by",
    "tell",
    "for",
    "from",
    "have",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "you",
}

# Provide backwards-compatible alias expected by older sentence-transformers
if not hasattr(huggingface_hub, "cached_download"):  # pragma: no cover - runtime compatibility shim
    from urllib.parse import urlparse

    from urllib.parse import urlparse

    def _legacy_cached_download(*, url, cache_dir=None, force_filename=None, use_auth_token=None, legacy_cache_layout=None, library_name=None, library_version=None, user_agent=None, **kwargs):  # type: ignore[override]
        """Map the legacy cached_download signature to hf_hub_download."""

        parsed = urlparse(url)
        parts = [segment for segment in parsed.path.split("/") if segment]

        repo_prefix = None
        if parts and parts[0] in {"models", "datasets", "spaces"}:
            repo_prefix = parts.pop(0)

        if "resolve" not in parts or len(parts) < 4:
            raise ValueError(f"Unsupported Hugging Face URL format: {url}")

        resolve_index = parts.index("resolve")
        repo_id_parts = parts[:resolve_index]
        revision = parts[resolve_index + 1]
        filename_parts = parts[resolve_index + 2 :]

        repo_id = "/".join(repo_id_parts)
        if repo_prefix:
            repo_id = f"{repo_prefix}/{repo_id}"

        filename = "/".join(filename_parts)

        download_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            revision=revision,
            cache_dir=cache_dir,
            local_dir=cache_dir,
            local_dir_use_symlinks=False,
            token=use_auth_token,
            library_name=library_name,
            library_version=library_version,
            user_agent=user_agent,
        )

        if force_filename and cache_dir:
            # hf_hub_download already respects filename relative path when local_dir is set, so just return path
            return download_path

        return download_path

    huggingface_hub.cached_download = _legacy_cached_download  # type: ignore[attr-defined]

try:  # pragma: no cover - import guard for optional reranker
    from sentence_transformers import CrossEncoder
except ImportError:  # pragma: no cover - fallback without reranker
    CrossEncoder = None  # type: ignore[misc]


class GeminiEmbeddingBackend:
    """Use Google Gemini embeddings for semantic retrieval."""

    def __init__(
        self,
        *,
        model_name: str = "text-embedding-004",
        api_key_env: str = "GEMINI_API_KEY",
        max_characters: int = 6000,
    ) -> None:
        self._model_name = model_name
        self._api_key_env = api_key_env
        self._max_characters = max_characters
        self._dimension: Optional[int] = None
        self._genai = None
        self._available = False
        self._init_error: Optional[str] = None

        api_key = os.getenv(self._api_key_env)
        if not api_key:
            self._init_error = f"Environment variable {self._api_key_env} not set"
            return

        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=api_key)
            self._genai = genai
            self._available = True
        except ImportError as exc:  # pragma: no cover - dependency optional
            self._init_error = f"google-generativeai not installed: {exc}"
        except Exception as exc:  # pragma: no cover - API init issues
            self._init_error = f"Failed to initialise Gemini embeddings: {exc}"

    def is_available(self) -> bool:
        return bool(self._available and self._genai is not None)

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        vectors: List[List[float]] = []

        for text in texts:
            vector = self._embed_single(text)
            if vector is None:
                vector = self._zero_vector()
            vectors.append(vector)

        matrix = np.asarray(vectors, dtype=np.float32)
        return self._normalize(matrix)

    def embed_query(self, text: str) -> np.ndarray:
        vector = self._embed_single(text)
        if vector is None:
            vector = self._zero_vector()
        array = np.asarray([vector], dtype=np.float32)
        return self._normalize(array)

    def _embed_single(self, text: str) -> Optional[List[float]]:
        if not self.is_available():
            return None

        content = (text or " ").strip()
        if len(content) > self._max_characters:
            content = content[: self._max_characters]

        try:
            response: Dict[str, Any] = self._genai.embed_content(  # type: ignore[operator]
                model=self._model_name,
                content=content,
            )
        except Exception:  # pragma: no cover - API call may fail at runtime
            return None

        vector = response.get("embedding")
        if vector is None:
            data = response.get("data")
            if isinstance(data, list) and data:
                vector = data[0].get("embedding")

        if not vector:
            return None

        if self._dimension is None:
            self._dimension = len(vector)

        return [float(value) for value in vector]

    def _zero_vector(self) -> List[float]:
        if self._dimension is None:
            # text-embedding-004 produces 768-dimensional vectors.
            self._dimension = 768
        return [0.0] * self._dimension

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        if matrix.size == 0:
            return matrix.astype(np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            normalized = np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms > 0)
        return normalized.astype(np.float32)


class SemanticSearchEngine:
    """Builds and queries a FAISS-backed semantic search index."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", *, embedding_backend: str = "gemini"):
        self.model_name = model_name
        self.embedding_backend = "gemini"
        if embedding_backend.lower().strip() != "gemini":
            print(
                f"Gemini embeddings are required; ignoring requested backend '{embedding_backend}'."
            )

        self._embedding_provider: Optional[GeminiEmbeddingBackend] = None
        self._vector_search_available = False

        self._ensure_gemini_provider()
        if not self._embedding_provider:
            raise RuntimeError("Gemini embedding provider not initialized")

        self.index = None
        self.documents: List[str] = []
        self.embeddings = None
        self.metadata: List[Dict[str, Any]] = []
        self.reranker_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self._reranker: Optional[Any] = None
        self._reranker_loaded = False
        self.keyword_index: DefaultDict[str, Set[int]] = defaultdict(set)

    def _ensure_gemini_provider(self) -> None:
        if self._embedding_provider and self._embedding_provider.is_available():
            return

        self._embedding_provider = GeminiEmbeddingBackend()
        if self._embedding_provider.is_available():
            return

        init_error = None
        if self._embedding_provider:
            init_error = self._embedding_provider.init_error

        message = init_error or "Gemini embedding service not available"
        raise RuntimeError(message)

    def build_knowledge_base(self, text_chunks):
        """Convert text chunks to embeddings and build a FAISS index."""
        if not text_chunks:
            print("No text chunks provided!")
            return

        print(f"Generating embeddings for {len(text_chunks)} chunks...")

        documents: List[str] = []
        metadata: List[Dict[str, Any]] = []

        for chunk in text_chunks:
            if isinstance(chunk, dict):
                text = str(chunk.get("text", "")).strip()
                documents.append(text)
                metadata.append({k: v for k, v in chunk.items() if k != "text"})
            else:
                documents.append(str(chunk).strip())
                metadata.append({})

        self.documents = documents
        self.metadata = metadata
        self._rebuild_keyword_index()

        self._ensure_gemini_provider()
        if not self._embedding_provider:
            raise RuntimeError("Gemini embedding provider not initialized")

        self.embeddings = self._embedding_provider.embed_documents(self.documents)

        # Build FAISS index for cosine similarity
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)

        self._vector_search_available = True

        print(f"Knowledge base built with {len(text_chunks)} chunks")

    def search(self, query, top_k=3):
        """Search for the most relevant documents."""
        if self.index is None or not self._vector_search_available:
            return []

        try:
            self._ensure_gemini_provider()
        except RuntimeError as exc:
            print(f"Gemini embeddings unavailable during search: {exc}")
            return []

        if not self._embedding_provider:
            print("Gemini embedding provider missing during search")
            return []

        query_embedding = self._embedding_provider.embed_query(query)

        # Perform similarity search
        scores, indices = self.index.search(query_embedding, top_k)

        # Return results with scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and score > 0.1:  # Filter very low scores
                metadata = self.metadata[idx] if idx < len(self.metadata) else {}
                results.append(
                    {
                        "text": self.documents[idx],
                        "score": float(score),
                        "relevance": "High" if score > 0.7 else "Medium" if score > 0.5 else "Low",
                        "metadata": metadata,
                    }
                )

        return results

    def keyword_search(
        self,
        query: str,
        max_results: int = 5,
        extra_terms: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fallback lexical search using keyword overlap."""

        tokens = {
            token
            for token in re.findall(r"\b\w+\b", query.lower())
            if len(token) > 2 and token not in STOPWORDS
        }

        if extra_terms:
            for term in extra_terms:
                if not term or len(term) <= 2:
                    continue
                lowered = term.lower()
                tokens.add(lowered)
                tokens.update(
                    {
                        sub_token
                        for sub_token in re.findall(r"\b\w+\b", lowered)
                        if len(sub_token) > 2 and sub_token not in STOPWORDS
                    }
                )

        tokens = self._expand_query_tokens(tokens)

        if not tokens:
            return []

        candidate_scores: Dict[int, float] = {}
        token_weights: Dict[str, float] = {}

        for token in tokens:
            base_weight = 1.0
            length_bonus = min(len(token) / 8.0, 1.5)
            emphasis_bonus = 0.75 if "intern" in token else 0.0
            weight = base_weight + length_bonus + emphasis_bonus
            token_weights[token] = weight

            for idx in self.keyword_index.get(token, set()):
                candidate_scores[idx] = candidate_scores.get(idx, 0.0) + weight

        if not candidate_scores:
            return []

        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda item: (item[1], len(self.documents[item[0]])),
            reverse=True,
        )

        total_weight = sum(token_weights.values()) or 1.0

        results: List[Dict[str, Any]] = []
        for idx, score in sorted_candidates[:max_results]:
            metadata = self.metadata[idx] if idx < len(self.metadata) else {}
            normalized = min(score / total_weight, 1.0)
            confidence = min(0.25 + normalized * 0.2, 0.65)
            results.append(
                {
                    "text": self.documents[idx],
                    "score": confidence,
                    "relevance": "Lexical",
                    "metadata": metadata,
                }
            )

        return results

    def _expand_query_tokens(self, tokens: Set[str]) -> Set[str]:
        expanded: Set[str] = set()

        for token in tokens:
            if not token or len(token) <= 2 or token in STOPWORDS:
                continue

            expanded.add(token)

            if token.endswith("ies") and len(token) > 3:
                expanded.add(token[:-3] + "y")

            if token.endswith("es") and len(token) > 4:
                expanded.add(token[:-2])

            if token.endswith("s") and len(token) > 3:
                expanded.add(token[:-1])

            if token.endswith("ing") and len(token) > 4:
                stem = token[:-3]
                expanded.add(stem)
                if not stem.endswith("e") and len(stem) > 2:
                    expanded.add(stem + "e")

        return {item for item in expanded if len(item) > 2 and item not in STOPWORDS}

    # ------------------------------------------------------------------
    # Advanced retrieval helpers
    def extract_relevant_sentences(
        self,
        query: str,
        results: List[Dict[str, Any]],
        *,
        max_sentences: int = 4,
    ) -> List[Dict[str, Any]]:
        """Select the most relevant sentences from search results."""

        candidates: List[Tuple[str, Dict[str, Any], float]] = []
        for rank, result in enumerate(results):
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            base_score = float(result.get("score", 0.0))

            for sentence in self._split_into_sentences(text):
                if len(sentence) < 24 or len(sentence) > 480:
                    continue
                candidates.append((sentence, metadata, base_score - rank * 0.01))

        if not candidates:
            return []

        keywords: Set[str] = {
            token
            for token in re.findall(r"\b\w+\b", query.lower())
            if len(token) > 2 and token not in STOPWORDS
        }

        reranker = self._get_reranker()
        if reranker is not None:
            pairs = [(query, sent) for sent, _, _ in candidates]
            try:
                scores = reranker.predict(pairs)  # type: ignore[no-untyped-call]
            except Exception:  # pragma: no cover - inference fallback
                scores = []
            else:
                ranked: List[Dict[str, Any]] = []
                for (sentence, metadata, base_score), score in zip(candidates, scores):
                    lowered = sentence.lower()
                    overlap = sum(lowered.count(keyword) for keyword in keywords)
                    if keywords and overlap == 0:
                        continue

                    ranked.append(
                        {
                            "sentence": sentence,
                            "metadata": metadata,
                            "score": float(score) + max(0.0, base_score) + overlap * 0.1,
                        }
                    )

                if ranked:
                    ranked.sort(key=lambda item: item["score"], reverse=True)
                    return ranked[:max_sentences]

        # Fallback scoring using keyword overlap + base score
        scored: List[Dict[str, Any]] = []
        for sentence, metadata, base_score in candidates:
            lowered = sentence.lower()
            overlap = sum(lowered.count(keyword) for keyword in keywords) or 0
            if not overlap and keywords:
                continue
            scored.append(
                {
                    "sentence": sentence,
                    "metadata": metadata,
                    "score": base_score + overlap,
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:max_sentences]

    # ------------------------------------------------------------------
    def preload_models(self) -> None:
        try:
            self._ensure_gemini_provider()
        except RuntimeError as exc:
            print(f"Unable to warm up Gemini embeddings: {exc}")

        reranker = self._get_reranker()
        if reranker is not None:
            print("Reranker model ready")

    def _get_reranker(self):
        if self._reranker_loaded:
            return self._reranker

        self._reranker_loaded = True
        if CrossEncoder is None:
            return None

        try:
            self._reranker = CrossEncoder(self.reranker_name)
        except Exception as exc:  # pragma: no cover - logging side-effect
            print(f"Could not load cross-encoder reranker: {exc}")
            self._reranker = None
        return self._reranker

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
        return sentences

    def _rebuild_keyword_index(self) -> None:
        """Construct an inverted index for lexical fallback search."""

        self.keyword_index = defaultdict(set)
        for idx, text in enumerate(self.documents):
            tokens = {
                token
                for token in re.findall(r"\b\w+\b", text.lower())
                if len(token) > 2 and token not in STOPWORDS
            }
            for token in tokens:
                variants = self._expand_query_tokens({token})
                if not variants:
                    continue
                for variant in variants:
                    self.keyword_index[variant].add(idx)

    def save_index(self, filepath):
        """Persist the FAISS index and associated metadata."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save FAISS index
        if self.index is None:
            raise ValueError("Cannot save knowledge base without a built index.")

        faiss.write_index(self.index, f"{filepath}.faiss")

        # Save documents and metadata
        with open(f"{filepath}_data.pkl", "wb") as file:
            pickle.dump(
                {
                    "documents": self.documents,
                    "embeddings": self.embeddings,
                    "metadata": self.metadata,
                    "embedding_backend": self.embedding_backend,
                },
                file,
            )

        print(f"Knowledge base saved to {filepath}")

    def load_index(self, filepath):
        """Load a previously saved FAISS index and metadata."""
        try:
            # Load FAISS index
            self.index = faiss.read_index(f"{filepath}.faiss")

            # Load documents and metadata
            with open(f"{filepath}_data.pkl", "rb") as file:
                data = pickle.load(file)
                self.documents = data["documents"]
                self.embeddings = data["embeddings"]
                self.metadata = data.get("metadata", [{} for _ in self.documents])
                saved_backend = data.get("embedding_backend", "gemini")
                if saved_backend != "gemini":
                    raise RuntimeError(
                        "Knowledge base was built without Gemini embeddings. Rebuild using Gemini to continue."
                    )
                self.embedding_backend = "gemini"
                self._rebuild_keyword_index()

            try:
                self._ensure_gemini_provider()
                self._vector_search_available = True
            except RuntimeError as exc:
                self._vector_search_available = False
                print(
                    "Gemini embeddings unavailable while loading knowledge base. "
                    "Vector search disabled until the service is restored."
                )
                print(f"  -> Details: {exc}")

            print(f"Knowledge base loaded from {filepath}")
            return True
        except Exception as exc:  # pragma: no cover - logging side-effect
            print(f"Failed to load knowledge base: {exc}")
            return False
