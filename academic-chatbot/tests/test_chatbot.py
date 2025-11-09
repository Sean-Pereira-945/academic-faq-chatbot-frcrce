"""Unit tests for AcademicFAQChatbot."""

from __future__ import annotations

import sys
import types
import unittest
from unittest import mock

sys.modules.setdefault("faiss", mock.MagicMock())

if "huggingface_hub" not in sys.modules:
    huggingface_stub = types.ModuleType("huggingface_hub")

    def _hf_hub_download(*args, **kwargs):  # pragma: no cover - test stub
        return "mock-path"

    huggingface_stub.hf_hub_download = _hf_hub_download  # type: ignore[attr-defined]
    huggingface_stub.cached_download = _hf_hub_download  # type: ignore[attr-defined]
    sys.modules["huggingface_hub"] = huggingface_stub

if "sentence_transformers" not in sys.modules:
    sentence_stub = types.ModuleType("sentence_transformers")
    sentence_stub.CrossEncoder = None  # type: ignore[attr-defined]
    sys.modules["sentence_transformers"] = sentence_stub

google_stub = sys.modules.setdefault("google", types.ModuleType("google"))
generativeai_stub = sys.modules.setdefault("google.generativeai", mock.MagicMock())
api_core_stub = sys.modules.setdefault("google.api_core", types.ModuleType("google.api_core"))
exceptions_stub = sys.modules.setdefault("google.api_core.exceptions", types.ModuleType("google.api_core.exceptions"))
exceptions_stub.NotFound = Exception  # type: ignore[attr-defined]
api_core_stub.exceptions = exceptions_stub  # type: ignore[attr-defined]
google_stub.generativeai = generativeai_stub  # type: ignore[attr-defined]
google_stub.api_core = api_core_stub  # type: ignore[attr-defined]

from chatbot import AcademicFAQChatbot


class AcademicFAQChatbotTests(unittest.TestCase):
    """Validate conversational behaviour of the chatbot."""

    @mock.patch("chatbot.SemanticSearchEngine")
    def test_preprocess_cleans_whitespace_and_punctuation(self, mock_engine):
        mock_engine.return_value.load_index.return_value = False
        bot = AcademicFAQChatbot()

        cleaned = bot.preprocess_query("  Hello, CAMPUS!!  ")
        self.assertEqual(cleaned, "hello campus!!")

    @mock.patch("chatbot.SemanticSearchEngine")
    def test_greeting_returns_welcome_message(self, mock_engine):
        mock_engine.return_value.load_index.return_value = False
        bot = AcademicFAQChatbot()

        message = bot.generate_response("Hey there")
        self.assertIn("Academic FAQ Assistant", message)

    @mock.patch("chatbot.SemanticSearchEngine")
    def test_not_trained_prompts_user_to_build_knowledge_base(self, mock_engine):
        mock_engine.return_value.load_index.return_value = False
        bot = AcademicFAQChatbot()

        message = bot.generate_response("What is the registration deadline?")
        self.assertIn("knowledge_base_builder.py", message)

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_high_confidence_result_returns_document_excerpt(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = [
            {
                "text": "Registration opens on August 1st for all returning students.",
                "score": 0.85,
                "relevance": "High",
                "metadata": {"source": "2023-2024 Handbook — page 5"},
            }
        ]
        engine_instance.documents = ["Registration opens on August 1st for all returning students."]

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = True
        rephraser_instance.compose_answer.return_value = (
            "Registration for returning students begins on August 1, according to [Source: 2023-2024 Handbook — page 5]."
        )
        rephraser_instance.rephrase.return_value = None

        bot = AcademicFAQChatbot()
        response = bot.generate_response("When does registration open?")

        self.assertEqual(
            "Registration for returning students begins on August 1, according to [Source: 2023-2024 Handbook — page 5].",
            response,
        )
        rephraser_instance.compose_answer.assert_called_once()

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_multiple_sentences_are_formatted_as_bullets(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = [
            {
                "text": (
                    "The library is open from 8 AM to 10 PM on weekdays. "
                    "Weekend access runs from 10 AM to 6 PM with limited services."
                ),
                "score": 0.82,
                "relevance": "High",
                "metadata": {"source": "Library Guide"},
            }
        ]
        engine_instance.extract_relevant_sentences.return_value = [
            {
                "sentence": "The library is open from 8 AM to 10 PM on weekdays.",
                "score": 0.81,
                "metadata": {"source": "Library Guide"},
            },
            {
                "sentence": "Weekend access runs from 10 AM to 6 PM with limited services.",
                "score": 0.79,
                "metadata": {"source": "Library Guide"},
            },
        ]

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = True
        rephraser_instance.compose_answer.return_value = (
            "Weekday library hours run 8 AM to 10 PM, while weekend service is limited to 10 AM–6 PM [Source: Library Guide]."
        )
        rephraser_instance.rephrase.return_value = None

        bot = AcademicFAQChatbot()
        response = bot.generate_response("What are the library hours and services?")

        self.assertEqual(
            "Weekday library hours run 8 AM to 10 PM, while weekend service is limited to 10 AM–6 PM [Source: Library Guide].",
            response,
        )
        rephraser_instance.compose_answer.assert_called_once()

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_gemini_rephraser_overrides_response(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = [
            {
                "text": "Graduation rehearsals take place the week before commencement.",
                "score": 0.91,
                "relevance": "High",
                "metadata": {"source": "Graduation Guide"},
            }
        ]
        engine_instance.extract_relevant_sentences.return_value = [
            {
                "sentence": "Graduation rehearsals take place the week before commencement.",
                "score": 0.9,
                "metadata": {"source": "Graduation Guide"},
            }
        ]

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = True
        rephraser_instance.compose_answer.return_value = "All graduation rehearsals happen the week before commencement."
        rephraser_instance.rephrase.return_value = None

        bot = AcademicFAQChatbot()
        response = bot.generate_response("When are graduation rehearsals held?")

        self.assertEqual(
            "All graduation rehearsals happen the week before commencement.",
            response,
        )
        rephraser_instance.compose_answer.assert_called_once()
        rephraser_instance.rephrase.assert_not_called()

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_rephrase_used_when_compose_returns_none(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = [
            {
                "text": "Orientation sessions run across the first week of term.",
                "score": 0.8,
                "relevance": "High",
                "metadata": {"source": "Orientation Guide"},
            }
        ]
        engine_instance.extract_relevant_sentences.return_value = [
            {
                "sentence": "Orientation sessions run across the first week of term.",
                "score": 0.79,
                "metadata": {"source": "Orientation Guide"},
            }
        ]

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = True
        rephraser_instance.compose_answer.return_value = None
        rephraser_instance.rephrase.return_value = "The handbook clarifies that orientation sessions run throughout the first week of term."

        bot = AcademicFAQChatbot()
        response = bot.generate_response("When are orientation sessions held?")

        self.assertEqual(
            "The handbook clarifies that orientation sessions run throughout the first week of term.",
            response,
        )
        rephraser_instance.compose_answer.assert_called_once()
        rephraser_instance.rephrase.assert_called_once()

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_direct_gemini_used_when_rephrase_fails(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = [
            {
                "text": (
                    "The library is open from 8 AM to 10 PM on weekdays. "
                    "Weekend access runs from 10 AM to 6 PM with limited services."
                ),
                "score": 0.82,
                "relevance": "High",
                "metadata": {"source": "Library Guide"},
            }
        ]
        engine_instance.extract_relevant_sentences.return_value = [
            {
                "sentence": "The library is open from 8 AM to 10 PM on weekdays.",
                "score": 0.81,
                "metadata": {"source": "Library Guide"},
            }
        ]

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = True
        rephraser_instance.compose_answer.return_value = None
        rephraser_instance.rephrase.return_value = None
        rephraser_instance.answer_without_context.return_value = "Please visit the library help desk for up-to-date hours."

        bot = AcademicFAQChatbot()
        response = bot.generate_response("What are the library hours?")

        self.assertEqual(
            "Please visit the library help desk for up-to-date hours.",
            response,
        )
        rephraser_instance.answer_without_context.assert_called_once()

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_no_results_escalates_to_gemini_direct_answer(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = []
        engine_instance.keyword_search.return_value = []
        engine_instance.extract_relevant_sentences.return_value = []

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = True
        rephraser_instance.expand_query.return_value = None
        rephraser_instance.compose_answer.return_value = None
        rephraser_instance.rephrase.return_value = None
        rephraser_instance.answer_without_context.return_value = "Please connect with financial aid for housing scholarship details."

        bot = AcademicFAQChatbot()
        response = bot.generate_response("What scholarships cover housing?")

        self.assertEqual(
            "Please connect with financial aid for housing scholarship details.",
            response,
        )

        rephraser_instance.answer_without_context.assert_called_once()
        args, kwargs = rephraser_instance.answer_without_context.call_args
        self.assertEqual(args[0], "What scholarships cover housing?")
        self.assertIsNone(kwargs.get("intent_hint"))

    @mock.patch("chatbot.GeminiRephraser")
    @mock.patch("chatbot.SemanticSearchEngine")
    def test_requires_gemini_key_when_unavailable(self, mock_engine, mock_rephraser):
        engine_instance = mock_engine.return_value
        engine_instance.load_index.return_value = True
        engine_instance.search.return_value = [
            {
                "text": "Tuition is due by the 5th business day of each term.",
                "score": 0.6,
                "relevance": "Medium",
                "metadata": {"source": "Tuition Policy"},
            }
        ]
        engine_instance.extract_relevant_sentences.return_value = []

        rephraser_instance = mock_rephraser.return_value
        rephraser_instance.is_available.return_value = False

        bot = AcademicFAQChatbot()
        response = bot.generate_response("When is tuition due?")

        self.assertIn("GEMINI_API_KEY", response)
        rephraser_instance.compose_answer.assert_not_called()
        rephraser_instance.rephrase.assert_not_called()


if __name__ == "__main__":
    unittest.main()
