"""Optional Gemini API integration for advanced answer rephrasing."""

from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency is exercised indirectly
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is optional at runtime
    load_dotenv = None  # type: ignore


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
            "You are an academic support assistant helping students understand handbook policies.\n"
            "Rewrite the bullet points below into a concise, friendly response that directly answers the student's question.\n"
            "Keep the tone neutral-professional, avoid inventing facts beyond the bullet points, and keep the answer under 160 words.\n"
            "Paraphrase the information in your own words rather than copying the bullets verbatim.\n"
            "If appropriate, use short paragraphs instead of bullets.\n\n"
            "Student question: \n"
            f"{query.strip()}\n\n"
            "Key facts from the handbook:\n"
            f"{bullet_list}\n\n"
            "Compose the final answer now."
        )

        try:
            result = self._model.generate_content(prompt)  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover - remote call may fail intermittently
            self._last_error = str(exc)
            return None

        candidates = getattr(result, "candidates", None)
        if not candidates:
            return None

        text_parts = []
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
                    text_parts.append(text.strip())
        final = "\n\n".join(fragment for fragment in text_parts if fragment)
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
            "You are an academic retrieval-augmented assistant."
            " Use only the supplied context to answer the student's question.\n"
            "Summarise the key points clearly, cite the origin of each fact using the wording [Source: <label>],"
            " and avoid introducing information that is not present in the context."
            " Paraphrase the ideas in your own words—do not quote the context verbatim unless a short phrase is essential."
            " Limit the response to around 180 words.\n\n"
            "Student question:\n"
            f"{query.strip()}\n\n"
            "Context snippets (each includes its source):\n"
            f"{context_block}\n\n"
            "Compose the answer now."
        )

        try:
            result = self._model.generate_content(prompt)  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover - remote call may fail intermittently
            self._last_error = str(exc)
            return None

        candidates = getattr(result, "candidates", None)
        if not candidates:
            return None

        text_parts = []
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
                    text_parts.append(text.strip())
        final = "\n\n".join(fragment for fragment in text_parts if fragment)
        return final.strip() or None

    @property
    def init_error(self) -> Optional[str]:
        """Expose the initialisation error for diagnostics/logging."""

        return self._init_error

    @property
    def last_error(self) -> Optional[str]:
        """Return the last error encountered during a generate call, if any."""

        return self._last_error

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


__all__ = ["GeminiRephraser"]
