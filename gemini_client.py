"""Optional Gemini API integration for advanced answer rephrasing."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency is exercised indirectly
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is optional at runtime
    load_dotenv = None  # type: ignore


@dataclass
class QueryExpansion:
    search_queries: List[str]
    focus_terms: List[str]
    intent: Optional[str] = None


class GeminiRephraser:
    """Wraps the Google Gemini API to polish chatbot answers.

    The rephraser is completely optional—if the dependency or API key is
    missing, it simply behaves like a no-op and the chatbot falls back to its
    deterministic formatting logic.
    """

    def __init__(
        self,
        *,
        model_name: str = "models/gemini-2.5-flash",
        api_key_env: str = "GEMINI_API_KEY",
    ) -> None:
        self._model_name = model_name
        self._api_key_env = api_key_env
        self._model = None
        self._available = False
        self._init_error: Optional[str] = None
        self._last_error: Optional[str] = None

        if load_dotenv is not None:
            load_dotenv()

        api_key = os.getenv(self._api_key_env)
        if not api_key:
            self._init_error = f"Environment variable {self._api_key_env} not set"
            return

        try:
            import google.generativeai as genai  # type: ignore

            try:
                from google.api_core.exceptions import NotFound  # type: ignore
            except ImportError:  # pragma: no cover - dependency optional
                NotFound = Exception  # type: ignore

            genai.configure(api_key=api_key)
            last_error: Optional[Exception] = None
            for candidate in self._resolve_model_candidates(self._model_name):
                try:
                    model = genai.GenerativeModel(candidate)
                    try:
                        model.count_tokens("ping")  # Quick capability check
                    except NotFound as exc:  # type: ignore[misc]
                        last_error = exc
                        continue

                    self._model = model
                    self._model_name = candidate
                    self._available = True
                    break
                except NotFound as exc:  # type: ignore[misc]
                    last_error = exc
                except Exception as exc:  # pragma: no cover - API init issues
                    last_error = exc

            if not self._available:
                detail = f": {last_error}" if last_error else ""
                self._init_error = f"Failed to initialise Gemini client{detail}"
        except ImportError as exc:  # pragma: no cover - dependency optional
            self._init_error = f"google-generativeai not installed: {exc}"
        except Exception as exc:  # pragma: no cover - API init issues
            self._init_error = f"Failed to initialise Gemini client: {exc}"

    def is_available(self) -> bool:
        """Return True if the Gemini rephraser can be used."""

        return bool(self._available and self._model is not None)

    def expand_query(self, query: str) -> Optional[QueryExpansion]:
        """Use Gemini to infer better search queries and focus terms."""

        if not self.is_available():
            return None

        prompt = (
            "You improve academic FAQ search queries."
            "\nQuestion: "
            f"{query.strip()}"
            "\nRespond with JSON containing keys search_queries (max 3 items),"
            " focus_terms (max 6 lower-case terms), and intent (short noun phrase)."
            "\nRules:"
            "\n- Each search query must be a concise phrase under 12 words"
            "\n- focus_terms must omit stopwords and punctuation"
            "\n- intent should summarise the student's goal in under 8 words"
            "\nOutput JSON only."
        )

        try:
            result = self._model.generate_content(prompt)  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover
            self._last_error = str(exc)
            return None

        payload = self._collect_text(result)
        if not payload:
            return None

        data = self._extract_json(payload)
        if not data:
            return None

        queries = [item.strip() for item in data.get("search_queries", []) if isinstance(item, str) and item.strip()]
        terms = [item.strip().lower() for item in data.get("focus_terms", []) if isinstance(item, str) and item.strip()]
        intent = data.get("intent")
        if intent and isinstance(intent, str):
            intent = intent.strip()

        if not queries and not terms:
            return None

        return QueryExpansion(search_queries=queries[:3], focus_terms=terms[:6], intent=intent or None)

    def rephrase(
        self,
        query: str,
        points: Iterable[str],
    ) -> Optional[str]:
        """Ask Gemini to craft a presentable answer.

        Returns ``None`` when the rephraser is not available or the API call
        fails for any reason, signalling the caller to fall back gracefully.
        """

        if not self.is_available():
            return None

        bullet_list = "\n".join(f"- {point}" for point in points if point.strip())
        if not bullet_list:
            return None

        prompt = (
            "You are an Academic FAQ Assistant. Provide direct, concise answers to student questions.\n\n"
            "TASK: Answer the question using ONLY the facts provided below.\n\n"
            "RULES:\n"
            "- Be direct and to-the-point - NO unnecessary elaboration\n"
            "- NO source citations or document references\n"
            "- Include specific details (dates, numbers, requirements) when available\n"
            "- Use simple, clear language\n"
            "- Keep response under 100 words\n"
            "- Use bullet points if listing multiple items\n"
            "- Do NOT add information beyond the provided facts\n\n"
            "STUDENT QUESTION:\n"
            f"{query.strip()}\n\n"
            "FACTS FROM DOCUMENTS:\n"
            f"{bullet_list}\n\n"
            "YOUR BRIEF ANSWER (no citations):"
        )

        try:
            result = self._model.generate_content(prompt)  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover - remote call may fail intermittently
            self._last_error = str(exc)
            return None

        final = self._collect_text(result)
        return final.strip() or None

    def compose_answer(
        self,
        query: str,
        contexts: Iterable[Dict[str, str]],
    ) -> Optional[str]:
        """Generate a fuller answer using the provided contextual snippets."""

        if not self.is_available():
            return None

        formatted_contexts = []
        for idx, context in enumerate(contexts, start=1):
            text = (context.get("text") or context.get("sentence") or "").strip()
            if not text:
                continue
            source = str(context.get("source") or context.get("document") or "Academic handbook").strip()
            formatted_contexts.append(f"[{idx}] {text}\nSource: {source}")

        if not formatted_contexts:
            return None

        context_block = "\n\n".join(formatted_contexts)

        prompt = (
            "You are an Academic FAQ Assistant. Answer questions directly and concisely based on the provided information.\n\n"
            "INSTRUCTIONS:\n"
            "1. Give direct, to-the-point answers WITHOUT citing sources or document names\n"
            "2. Answer ONLY based on the provided context - do not use external knowledge\n"
            "3. If context is insufficient, say: 'I don't have complete information about this. Please contact the academic office.'\n"
            "4. Be specific with dates, numbers, and requirements\n"
            "5. Use clear, simple language - avoid unnecessary elaboration\n"
            "6. Keep responses brief (80-120 words maximum)\n"
            "7. Use bullet points or numbered lists when listing multiple items\n"
            "8. NO source citations, NO document references, NO [Source: ...] tags\n\n"
            "STUDENT QUESTION:\n"
            f"{query.strip()}\n\n"
            "INFORMATION FROM DOCUMENTS:\n"
            f"{context_block}\n\n"
            "YOUR DIRECT ANSWER (no citations):"
        )

        try:
            result = self._model.generate_content(prompt)  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover - remote call may fail intermittently
            self._last_error = str(exc)
            return None

        final = self._collect_text(result)
        return final.strip() or None

    @property
    def init_error(self) -> Optional[str]:
        """Expose the initialisation error for diagnostics/logging."""

        return self._init_error

    @property
    def last_error(self) -> Optional[str]:
        """Return the last error encountered during a generate call, if any."""

        return self._last_error

    def _collect_text(self, result) -> str:
        candidates = getattr(result, "candidates", None)
        if not candidates:
            return ""

        snippets: List[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    snippets.append(text.strip())

        return "\n\n".join(fragment for fragment in snippets if fragment)

    @staticmethod
    def _extract_json(payload: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"\{.*\}", payload, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _resolve_model_candidates(preferred: str) -> List[str]:
        base_candidates = [
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.0-flash",
        ]

        variants: List[str] = []
        if preferred:
            variants.append(preferred)
            if preferred.startswith("models/"):
                variants.append(preferred.split("models/", 1)[-1])
            else:
                variants.append(f"models/{preferred}")

        candidates: List[str] = []
        for candidate in variants + base_candidates:
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        return candidates


__all__ = ["GeminiRephraser", "QueryExpansion"]
