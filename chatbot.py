"""Core chatbot logic for the Academic FAQ assistant."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Set

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

from gemini_client import GeminiRephraser, QueryExpansion
from semantic_search import STOPWORDS, SemanticSearchEngine


SYNONYM_MAP: Dict[str, Set[str]] = {
    "financial aid": {"scholarship", "tuition assistance", "fafsa", "aid"},
    "scholarship": {"financial aid", "tuition assistance"},
    "aid": {"financial aid"},
    "drop a course": {"withdraw", "course withdrawal", "withdraw from a class"},
    "drop": {"withdraw"},
    "withdraw": {"drop", "course withdrawal"},
    "register": {"enroll", "registration"},
    "registration": {"enroll", "course sign up"},
    "academic calendar": {"term dates", "important dates", "schedule"},
    "advisor": {"counselor", "academic advisor"},
    "academic advisor": {"counselor", "advisor"},
    "counselor": {"advisor"},
    "library": {"media center", "learning commons"},
    "library hours": {"library schedule", "media center hours"},
    "health services": {"wellness", "nurse", "medical services"},
    "health": {"wellness"},
    "student id": {"identification card", "id card", "school id"},
    "parking": {"vehicle parking", "car parking", "student parking"},
    "refund": {"tuition refund", "reimbursement"},
    "exam": {"assessment", "test"},
    "transcript": {"academic record", "official record"},
}


class AcademicFAQChatbot:
    """Academic FAQ chatbot powered by a semantic search engine."""

    def __init__(self) -> None:
        import logging
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🔄 Initializing AcademicFAQChatbot...")
        
        try:
            self.search_engine = SemanticSearchEngine(embedding_backend="gemini")
            self.logger.info("✅ Search engine initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize search engine: {e}")
            raise
            
        self.is_trained = False

        try:
            self.rephraser = GeminiRephraser()
            self.logger.info(f"✅ Rephraser initialized (available: {self.rephraser.is_available()})")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize rephraser: {e}")
            raise

        if os.path.exists("models/academic_faq.faiss"):
            self.logger.info("📂 Found knowledge base files, loading...")
            try:
                self.is_trained = self.search_engine.load_index("models/academic_faq")
                self.logger.info(f"✅ Knowledge base loaded. Is trained: {self.is_trained}")
                if self.is_trained and self.search_engine.embedding_backend != "gemini":
                    self.logger.warning(
                        "⚠️  Loaded knowledge base was built without Gemini embeddings. "
                        "Rebuild with `python knowledge_base_builder.py --embedding-backend gemini` for best results."
                    )
            except Exception as e:
                self.logger.error(f"❌ Failed to load knowledge base: {e}")
                raise
        else:
            self.logger.warning("⚠️  Knowledge base not found at models/academic_faq.faiss")

        self.greetings: List[str] = [
            "hello",
            "hi",
            "hey",
            "greetings",
            "good morning",
            "good afternoon",
        ]
        self.farewells: List[str] = [
            "bye",
            "goodbye",
            "see you",
            "thanks",
            "thank you",
        ]

    def preprocess_query(self, query: str) -> str:
        """Clean and preprocess user query."""
        lowered = re.sub(r"\s+", " ", query.strip().lower())
        return re.sub(r"[^\w\s\?\!\.]", "", lowered)

    def is_greeting(self, query: str) -> bool:
        """Check if query is a greeting."""
        return self._contains_phrase(query, self.greetings)

    def is_farewell(self, query: str) -> bool:
        """Check if query is a farewell."""
        return self._contains_phrase(query, self.farewells)

    def generate_response(self, query: str) -> str:
        """Generate response based on user query."""
        if not query or len(query.strip()) < 2:
            return "Please ask a specific question about academic policies or procedures."

        processed_query = self.preprocess_query(query)

        if self.is_greeting(processed_query):
            return (
                "Hello! I'm your Academic FAQ Assistant. I can help you with questions about academic policies, "
                "deadlines, course registration, and university procedures. What would you like to know?"
            )

        if self.is_farewell(processed_query):
            return (
                "Thank you for using the Academic FAQ Assistant! Feel free to ask me any academic questions anytime. "
                "Have a great day!"
            )

        if not self.is_trained:
            return (
                "I'm still learning! The knowledge base hasn't been built yet. "
                "Please run the knowledge_base_builder.py script first."
            )

        expanded_query, expanded_terms = self._expand_query(processed_query)
        intent_hint: Optional[str] = None

        llm_expansion = self._expand_query_with_gemini(processed_query)
        if llm_expansion:
            for term in llm_expansion.focus_terms:
                cleaned = term.strip()
                if cleaned:
                    expanded_terms.add(cleaned.lower())

            extra_queries = [item for item in llm_expansion.search_queries if item]
            if extra_queries:
                expansion_text = " ".join(extra_queries)
                expanded_query = f"{expanded_query} {expansion_text}".strip()

            if llm_expansion.intent:
                intent_hint = llm_expansion.intent

        results = self.search_engine.search(expanded_query, top_k=8)

        if not results or results[0]["score"] < 0.3:
            lexical_results = self.search_engine.keyword_search(
                expanded_query,
                max_results=5,
                extra_terms=expanded_terms,
            )
            if lexical_results:
                results = lexical_results
            else:
                return (
                    "After reviewing the handbook, I couldn't locate a dedicated section on that topic. "
                    "Please connect with the academic office for the latest guidance, and I can help search the handbook with different wording if you'd like."
                )

        sentence_hits = self.search_engine.extract_relevant_sentences(
            processed_query,
            results,
            max_sentences=4,
        )

        if not self.rephraser.is_available():
            return self._gemini_required_message()

        presentable_response = self._compose_presentable_answer(
            query,
            processed_query,
            sentence_hits,
            results,
            expanded_terms,
            intent_hint=intent_hint,
        )
        if presentable_response:
            return presentable_response

        return self._gemini_required_message()

    def get_stats(self) -> str:
        """Get chatbot statistics."""
        if not self.is_trained:
            return "Knowledge base not loaded"

        return f"Knowledge base contains {len(self.search_engine.documents)} text chunks"

    # ------------------------------------------------------------------
    # Helper methods
    def _contains_phrase(self, text: str, phrases: List[str]) -> bool:
        normalized = text.lower()
        tokens = set(re.findall(r"\b\w+\b", normalized))

        for phrase in phrases:
            lowered = phrase.lower()
            if " " in lowered:
                if lowered in normalized:
                    return True
            elif lowered in tokens:
                return True

        return False

    def _expand_query(self, query: str) -> tuple[str, Set[str]]:
        tokens = self._extract_tokens(query)
        expanded_terms: Set[str] = set()
        normalized = query.lower()

        for phrase, synonyms in SYNONYM_MAP.items():
            if (" " in phrase and phrase in normalized) or (phrase in tokens):
                expanded_terms.update(syn.lower() for syn in synonyms)

        term_set = set(tokens)
        term_set.update(expanded_terms)

        if expanded_terms:
            expansion_text = " ".join(sorted(expanded_terms))
            expanded_query = f"{query} {expansion_text}".strip()
        else:
            expanded_query = query

        return expanded_query, term_set

    def _expand_query_with_gemini(self, query: str) -> Optional[QueryExpansion]:
        if not self.rephraser.is_available():
            return None

        try:
            expansion = self.rephraser.expand_query(query)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.debug(f"Gemini query expansion failed: {exc}")
            return None

        if not isinstance(expansion, QueryExpansion):
            return None

        return expansion

    @staticmethod
    def _extract_tokens(text: str) -> Set[str]:
        return {
            token
            for token in re.findall(r"\b\w+\b", text.lower())
            if len(token) > 2 and token not in STOPWORDS
        }

    @staticmethod
    def _clean_sentence(text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if cleaned and cleaned[-1] not in {".", "!", "?"}:
            cleaned += "."
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        return cleaned

    def _compose_presentable_answer(
        self,
        raw_query: str,
        processed_query: str,
        sentence_hits: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        expanded_terms: Set[str],
        *,
        intent_hint: Optional[str] = None,
    ) -> str:
        query_tokens = self._extract_tokens(processed_query)
        query_tokens.update({term.lower() for term in expanded_terms if len(term) > 2})

        sentences = self._gather_sentences_from_hits(sentence_hits, limit=4)

        if len(sentences) < 2:
            supplemental = self._gather_sentences_from_results(
                results,
                query_tokens,
                limit=4,
            )
            seen = {self._normalize_sentence(item.get("sentence", "")) for item in sentences}
            for candidate in supplemental:
                normalized = self._normalize_sentence(candidate.get("sentence", ""))
                if not normalized or normalized in seen:
                    continue
                sentences.append(candidate)
                seen.add(normalized)
                if len(sentences) >= 4:
                    break

        if not sentences:
            return ""

        return self._format_presentable_answer(raw_query, sentences, results, intent_hint=intent_hint)

    def _gather_sentences_from_hits(
        self,
        sentence_hits: List[Dict[str, Any]],
        *,
        limit: int,
    ) -> List[Dict[str, Any]]:
        sentences: List[Dict[str, Any]] = []
        seen: Set[str] = set()

        for hit in sentence_hits:
            sentence = str(hit.get("sentence", "")).strip()
            if not sentence:
                continue

            metadata = dict(hit.get("metadata", {}) or {})

            normalized = self._normalize_sentence(sentence)
            if normalized in seen:
                continue

            seen.add(normalized)
            sentences.append({"sentence": sentence, "metadata": metadata})

            if len(sentences) >= limit:
                break

        return sentences

    def _gather_sentences_from_results(
        self,
        results: List[Dict[str, Any]],
        query_tokens: Set[str],
        *,
        limit: int,
    ) -> List[Dict[str, Any]]:
        candidates: List[tuple[float, str, Dict[str, Any]]] = []

        for rank, result in enumerate(results):
            text = str(result.get("text", "")).strip()
            if not text:
                continue

            base_score = float(result.get("score", 0.0)) - rank * 0.05
            metadata = dict(result.get("metadata", {}) or {})

            for sentence in self._split_into_sentences(text):
                stripped = sentence.strip()
                if len(stripped) < 40 or len(stripped) > 400:
                    continue

                score = base_score + self._score_sentence(stripped, query_tokens)
                if score <= 0:
                    continue

                candidates.append((score, stripped, metadata))

        if not candidates:
            return []

        candidates.sort(key=lambda item: item[0], reverse=True)

        sentences: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for _, sentence, metadata in candidates:
            normalized = self._normalize_sentence(sentence)
            if normalized in seen:
                continue
            seen.add(normalized)
            sentences.append({"sentence": sentence, "metadata": metadata})
            if len(sentences) >= limit:
                break

        return sentences

    def _format_presentable_answer(
        self,
        raw_query: str,
        sentences: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        *,
        intent_hint: Optional[str] = None,
    ) -> str:
        intro = self._build_intro(raw_query, intent_hint)
        question_type = self._get_question_type(raw_query)
        topic_phrase = self._derive_topic_phrase(raw_query)

        formatted_points: List[str] = []
        for entry in sentences:
            sentence_text = str(entry.get("sentence", "")).strip()
            if not sentence_text:
                continue
            rephrased = self._rephrase_sentence(sentence_text, question_type, topic_phrase)
            if rephrased:
                formatted_points.append(rephrased)

        if not formatted_points:
            first_sentence = next(
                (str(entry.get("sentence", "")).strip() for entry in sentences if str(entry.get("sentence", "")).strip()),
                "",
            )
            if first_sentence:
                formatted_points = [self._clean_sentence(first_sentence)]

        def _trim_snippet(text: str, limit: int = 800) -> str:
            cleaned = str(text).strip()
            if len(cleaned) > limit:
                return cleaned[: limit - 3].rstrip() + "..."
            return cleaned

        chunk_snippets = [
            {
                "text": _trim_snippet(result.get("text", "")),
                "source": self._format_source_label(result.get("metadata", {})),
            }
            for result in results
            if str(result.get("text", "")).strip()
        ]
        sentence_snippets = [
            {
                "text": _trim_snippet(entry.get("sentence", ""), limit=400),
                "source": self._format_source_label(entry.get("metadata", {})),
            }
            for entry in sentences
            if str(entry.get("sentence", "")).strip()
        ]

        snippets_for_llm: List[Dict[str, str]] = []
        if sentence_snippets:
            snippets_for_llm.extend(sentence_snippets[:6])
        if chunk_snippets and len(snippets_for_llm) < 3:
            needed = 6 - len(snippets_for_llm)
            snippets_for_llm.extend(chunk_snippets[: max(needed, 3)])
        if not snippets_for_llm:
            snippets_for_llm = chunk_snippets or sentence_snippets

        llm_answer: Optional[str] = None
        llm_answer = self.rephraser.compose_answer(raw_query, snippets_for_llm)
        if not llm_answer:
            llm_answer = self.rephraser.rephrase(raw_query, formatted_points)

        if llm_answer:
            return llm_answer

        fallback_points = formatted_points or [self._clean_sentence(str(sentences[0].get("sentence", "")))]
        fallback_points = [point for point in fallback_points if point]

        fallback_sections: List[str] = []
        if intro:
            fallback_sections.append(intro)

        if fallback_points:
            bullets = "\n".join(f"- {point}" for point in fallback_points)
            fallback_sections.append(bullets)
        source_labels: List[str] = []
        for entry in sentences:
            label = self._format_source_label(entry.get("metadata", {}))
            if label:
                source_labels.append(label)

        if not source_labels:
            for result in results:
                label = self._format_source_label(result.get("metadata", {}))
                if label:
                    source_labels.append(label)

        if source_labels:
            ordered_sources: List[str] = []
            for label in source_labels:
                if label not in ordered_sources:
                    ordered_sources.append(label)
            fallback_sections.append("Sources: " + ", ".join(ordered_sources))

        fallback_text = "\n\n".join(section.strip() for section in fallback_sections if section.strip())

        if fallback_text:
            return fallback_text

        return self._gemini_required_message()

    def _format_source_label(self, metadata: Dict[str, Any]) -> str:
        if not metadata:
            return "Academic handbook"

        source = metadata.get("source")
        if source:
            return str(source)

        document = metadata.get("document_name") or metadata.get("document_path") or metadata.get("document_type")
        page = metadata.get("page")

        if document and page:
            return f"{document} — page {page}"

        if document:
            return str(document)

        return "Academic handbook"

    @staticmethod
    def _gemini_required_message() -> str:
        return (
            "This assistant now relies on Google Gemini to craft answers. "
            "Please make sure the GEMINI_API_KEY environment variable is set and the google-generativeai package is installed, then try again."
        )

    @staticmethod
    def _normalize_sentence(sentence: str) -> str:
        return re.sub(r"\s+", " ", sentence.strip().lower())

    def _score_sentence(self, sentence: str, query_tokens: Set[str]) -> float:
        lowered = sentence.lower()
        token_matches = sum(1 for token in query_tokens if token in lowered)
        length_penalty = len(sentence) / 250
        return token_matches - length_penalty

    def _build_intro(self, raw_query: str, intent_hint: Optional[str] = None) -> str:
        cleaned = raw_query.strip() or "your question"
        cleaned = cleaned.rstrip("?!.")
        if not cleaned:
            cleaned = "your question"
        if intent_hint:
            return f"Here's what the handbook clarifies about {intent_hint.lower()}:"
        return f"Here's what the handbook clarifies about \"{cleaned}\":"

    @staticmethod
    def _get_question_type(raw_query: str) -> str:
        normalized = raw_query.strip().lower()
        for keyword in ("when", "where", "how", "who", "why", "what"):
            if normalized.startswith(keyword):
                return keyword
        return "yesno" if normalized.startswith(("is", "are", "can", "does", "do", "will", "should")) else "other"

    def _derive_topic_phrase(self, raw_query: str) -> str:
        normalized = re.sub(r"[^\w\s]", " ", raw_query.lower())
        tokens = [token for token in normalized.split() if token]
        skip = {
            "what",
            "when",
            "where",
            "why",
            "who",
            "how",
            "is",
            "are",
            "can",
            "does",
            "do",
            "will",
            "should",
            "could",
            "would",
            "the",
            "a",
            "an",
            "please",
            "tell",
            "me",
        }

        filtered = [token for token in tokens if token not in skip and token not in STOPWORDS]

        if not filtered:
            return "this topic"

        replacements = {
            "open": "opening",
            "start": "start",
            "begin": "beginning",
            "deadline": "deadline",
            "due": "due date",
        }

        if filtered[-1] in replacements:
            filtered[-1] = replacements[filtered[-1]]

        phrase = " ".join(filtered[:6]).strip()
        return phrase if phrase else "this topic"

    def _rephrase_sentence(self, sentence: str, question_type: str, topic_phrase: str) -> str:
        cleaned = self._clean_sentence(sentence)
        if not cleaned:
            return ""

        base = cleaned.rstrip(".?!")
        body = self._lowercase_first(base)

        topic_text = topic_phrase if topic_phrase and topic_phrase != "this topic" else "this topic"

        if question_type == "when":
            prefix = f"The timeline for {topic_text} is that"
        elif question_type == "where":
            prefix = f"Regarding where {topic_text} applies,"
        elif question_type == "how":
            prefix = f"To address how {topic_text} works,"
        elif question_type == "who":
            prefix = f"In terms of who is involved with {topic_text},"
        elif question_type == "why":
            prefix = f"The reason for {topic_text} is that"
        elif question_type == "what":
            prefix = f"Concerning {topic_text},"
        elif question_type == "yesno":
            prefix = f"The handbook clarifies that"
        else:
            prefix = "It clarifies that"

        if body:
            return f"{prefix} {body}."
        return cleaned

    @staticmethod
    def _lowercase_first(text: str) -> str:
        return text[0].lower() + text[1:] if text else text

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        return [segment for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]


__all__ = ["AcademicFAQChatbot"]
