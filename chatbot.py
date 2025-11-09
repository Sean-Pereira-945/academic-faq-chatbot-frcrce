"""Core chatbot logic for the Financial Guidance assistant."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

from gemini_client import GeminiRephraser, QueryExpansion
from semantic_search import STOPWORDS, SemanticSearchEngine


SYNONYM_MAP: Dict[str, Set[str]] = {
    "interest rate": {"apr", "borrowing cost", "rate"},
    "loan": {"credit", "financing", "borrow"},
    "mortgage": {"home loan", "housing finance"},
    "investment": {"portfolio", "invest", "assets"},
    "retirement": {"401k", "pension", "superannuation"},
    "credit card": {"card", "revolving credit", "plastic"},
    "savings": {"deposit", "emergency fund", "cash reserve"},
    "budget": {"spending plan", "cash flow", "expenses"},
    "insurance": {"coverage", "policy", "premium"},
    "tax": {"taxes", "taxation", "irs"},
    "stock market": {"equities", "shares", "markets"},
    "mutual fund": {"mf", "investment fund"},
    "certificate of deposit": {"cd", "fixed deposit"},
    "emergency fund": {"rainy day fund", "safety net"},
    "credit score": {"fico", "credit history"},
    "debt": {"liability", "obligation"},
    "capital gains": {"investment gains", "realised profit"},
    "dividend": {"payout", "distribution"},
    "financial advisor": {"planner", "wealth manager"},
    "estate planning": {"will", "inheritance", "trust"},
}

INDEX_STEMS: Tuple[str, ...] = (
    "models/financial_advisor",
    "models/academic_faq",
)


class FinancialAdvisorChatbot:
    """Provide financial guidance by searching curated resources."""

    def __init__(self) -> None:
        import logging
        self.logger = logging.getLogger(__name__)

        self.logger.info("Initializing FinancialAdvisorChatbot")

        try:
            self.search_engine = SemanticSearchEngine(embedding_backend="gemini")
            self.logger.info("Search engine initialized")
        except Exception as e:
            self.logger.error("Failed to initialize search engine: %s", e)
            raise
            
        self.is_trained = False
        self.index_stem: Optional[str] = None

        try:
            self.rephraser = GeminiRephraser()
            self.logger.info("Rephraser initialized (available: %s)", self.rephraser.is_available())
        except Exception as e:
            self.logger.error("Failed to initialize rephraser: %s", e)
            raise

        for stem in INDEX_STEMS:
            faiss_path = f"{stem}.faiss"
            if not os.path.exists(faiss_path):
                continue

            self.logger.info("Found knowledge base candidate at %s", faiss_path)
            try:
                if self.search_engine.load_index(stem):
                    self.is_trained = True
                    self.index_stem = stem
                    self.logger.info("Knowledge base loaded from %s", stem)
                    break
            except Exception as e:
                self.logger.error("Failed to load knowledge base from %s: %s", stem, e)
                raise

        if not self.is_trained:
            self.logger.warning(
                "Knowledge base not found. Build it with `python knowledge_base_builder.py` to unlock financial answers."
            )

        try:
            self.logger.info("Warming up embedding models and reranker")
            self.search_engine.preload_models()
        except Exception as exc:
            self.logger.warning("Warm-up skipped: %s", exc)

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
            return "Please ask a specific question about your finances or money decisions."

        processed_query = self.preprocess_query(query)

        if self.is_greeting(processed_query):
            return (
                "Hello! I'm your personal finance assistant. Ask me about saving, investing, credit, taxes, or any"
                " money goal you're working on. How can I help today?"
            )

        if self.is_farewell(processed_query):
            return (
                "Thanks for chatting about your finances! If more money questions pop up, I'm here 24/7."
            )

        if not self.is_trained:
            kb_message = (
                "I'm still building your financial knowledge base. Please run knowledge_base_builder.py so I can"
                " provide tailored answers from your documents and bookmarked sites."
            )

            direct_answer = self._answer_directly_with_gemini(query, intent_hint=None)
            if direct_answer:
                return (
                    f"{kb_message}\n\nIn the meantime, here's what Gemini suggests based on your question:\n\n"
                    f"{direct_answer}"
                )

            return kb_message

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
                direct_answer = self._answer_directly_with_gemini(query, intent_hint)
                if direct_answer:
                    return direct_answer
                return (
                    "I couldn't find a clear answer in your financial documents. "
                    "Consider reaching out to a licensed advisor for personalised guidance, and I can keep searching if you share more details."
                )

        sentence_hits = self.search_engine.extract_relevant_sentences(
            processed_query,
            results,
            max_sentences=4,
        )

        use_rephraser = self.rephraser.is_available()
        if not use_rephraser:
            return self._gemini_required_message()

        presentable_response = self._compose_presentable_answer(
            query,
            processed_query,
            sentence_hits,
            results,
            expanded_terms,
            use_rephraser=True,
            intent_hint=intent_hint,
        )

        if presentable_response:
            return presentable_response

        direct_answer = self._answer_directly_with_gemini(query, intent_hint)
        if direct_answer:
            return direct_answer

        return self._gemini_required_message()

    def get_stats(self) -> str:
        """Get chatbot statistics."""
        if not self.is_trained:
            return "Financial knowledge base not loaded"

        return f"Financial knowledge base contains {len(self.search_engine.documents)} text chunks"

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
        use_rephraser: bool,
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

        return self._format_presentable_answer(
            raw_query,
            sentences,
            results,
            use_rephraser=use_rephraser,
            intent_hint=intent_hint,
        )

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
                if len(stripped) < 24 or len(stripped) > 480:
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
        use_rephraser: bool,
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
        if use_rephraser and self.rephraser.is_available():
            llm_answer = self.rephraser.compose_answer(
                raw_query,
                snippets_for_llm,
                intent_hint=intent_hint,
            )
            if not llm_answer:
                llm_answer = self.rephraser.rephrase(
                    raw_query,
                    formatted_points,
                    intent_hint=intent_hint,
                )

        if llm_answer:
            return self._deduplicate_text(llm_answer)

        if use_rephraser:
            return ""

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
        fallback_text = self._deduplicate_text(fallback_text)

        if fallback_text:
            return fallback_text

        return ""

    def _answer_directly_with_gemini(
        self,
        raw_query: str,
        intent_hint: Optional[str],
    ) -> Optional[str]:
        if not self.rephraser.is_available():
            return None

        try:
            direct = self.rephraser.answer_without_context(raw_query, intent_hint=intent_hint)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.debug(f"Gemini direct answer failed: {exc}")
            return None

        if not direct:
            return None

        return self._deduplicate_text(direct)

    def _format_source_label(self, metadata: Dict[str, Any]) -> str:
        if not metadata:
            return "Financial reference"

        source = metadata.get("source")
        if source:
            return str(source)

        document = metadata.get("document_name") or metadata.get("document_path") or metadata.get("document_type")
        page = metadata.get("page")

        if document and page:
            return f"{document} — page {page}"

        if document:
            return str(document)

        return "Financial reference"

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
            return f"Here's what your financial knowledge base highlights about {intent_hint.lower()}:"
        return f"Here's what your financial knowledge base highlights about \"{cleaned}\":"

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
            prefix = "Our financial resources indicate that"
        else:
            prefix = "Our research shows that"

        if body:
            return f"{prefix} {body}."
        return cleaned

    @staticmethod
    def _lowercase_first(text: str) -> str:
        return text[0].lower() + text[1:] if text else text

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        return [segment for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]

    @staticmethod
    def _deduplicate_text(text: str) -> str:
        if not text:
            return ""

        lines = text.splitlines()
        seen: Set[str] = set()
        deduped: List[str] = []

        for line in lines:
            if not line.strip():
                # Preserve single blank lines while collapsing runs
                if deduped and deduped[-1] != "":
                    deduped.append("")
                continue

            normalized = re.sub(r"\s+", " ", line.strip()).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(line.rstrip())

        # Remove trailing blank line if present
        while deduped and not deduped[-1].strip():
            deduped.pop()

        return "\n".join(deduped).strip()


AcademicFAQChatbot = FinancialAdvisorChatbot

__all__ = ["FinancialAdvisorChatbot", "AcademicFAQChatbot"]
