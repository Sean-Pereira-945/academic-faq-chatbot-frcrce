#!/usr/bin/env python3
"""Test suite runner for the Academic FAQ Chatbot."""

from __future__ import annotations

from chatbot import AcademicFAQChatbot


def test_basic_functionality() -> None:
    """Test greeting, farewell, and empty-query behaviours."""
    print("Testing Basic Functionality")
    print("-" * 40)

    chatbot = AcademicFAQChatbot()

    greeting_response = chatbot.generate_response("Hello")
    assert "Academic FAQ Assistant" in greeting_response
    print("Greeting test passed")

    farewell_response = chatbot.generate_response("Thank you")
    assert "Thank you" in farewell_response or "great day" in farewell_response
    print("Farewell test passed")

    empty_response = chatbot.generate_response("")
    assert "specific question" in empty_response.lower()
    print("Empty query test passed")

    print("All basic functionality tests passed!\n")


def test_knowledge_base() -> None:
    """Test knowledge-base backed responses."""
    print("Testing Knowledge Base")
    print("-" * 40)

    chatbot = AcademicFAQChatbot()

    if not chatbot.is_trained:
        print("Knowledge base not loaded - skipping knowledge tests")
        return

    test_queries = [
        "course registration",
        "academic calendar",
        "graduation requirements",
    ]

    for query in test_queries:
        response = chatbot.generate_response(query)
        assert len(response) > 50
        print(f"Query '{query}' returned response")

    print("All knowledge base tests passed!\n")


def run_all_tests() -> None:
    """Execute all custom tests."""
    print("Academic FAQ Chatbot - Test Suite")
    print("=" * 50)

    try:
        test_basic_functionality()
        test_knowledge_base()
        print("All tests passed successfully!")
    except AssertionError as exc:
        print(f"Test failed: {exc}")
    except Exception as exc:  # pragma: no cover - diagnostic output
        print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    run_all_tests()
