#!/usr/bin/env python3
"""Evaluation framework for the Academic FAQ Chatbot."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from chatbot import AcademicFAQChatbot


class ChatbotEvaluator:
    """Provides automated and manual evaluation helpers for the chatbot."""

    def __init__(self, chatbot: AcademicFAQChatbot) -> None:
        self.chatbot = chatbot
        self.test_queries: List[str] = [
            "What is the deadline for course registration?",
            "How do I drop a course?",
            "What are the library hours?",
            "When do classes start?",
            "What is the refund policy?",
            "How do I apply for financial aid?",
            "What are the graduation requirements?",
            "How do I change my major?",
            "What is the attendance policy?",
            "How do I access my transcript?",
            "What are the late fee charges?",
            "How do I register for classes?",
            "What is the academic calendar?",
            "How do I contact academic advisors?",
            "What are the exam policies?",
            "How do I appeal a grade?",
            "What parking is available?",
            "How do I get a student ID?",
            "What health services are available?",
            "How do I join student organizations?",
        ]

    def evaluate_response_time(self, query: str) -> Tuple[str, float]:
        """Measure response time for a single query."""
        start_time = time.time()
        response = self.chatbot.generate_response(query)
        end_time = time.time()
        return response, end_time - start_time

    def manual_relevance_score(self, query: str, response: str) -> int:
        """Prompt user for a manual relevance score (1-5)."""
        print(f"\nQuery: {query}")
        print(f"Response: {response}")
        print("\nRelevance Scale:")
        print("5 - Perfect Answer")
        print("4 - Good Answer")
        print("3 - Related but incomplete")
        print("2 - Somewhat related")
        print("1 - Irrelevant")

        while True:
            try:
                score = int(input("Enter relevance score (1-5): "))
                if 1 <= score <= 5:
                    return score
                print("Please enter a number between 1 and 5")
            except ValueError:
                print("Please enter a valid number")

    def automated_evaluation(self) -> List[Dict[str, Any]]:
        """Run automated evaluation metrics across test queries."""
        results: List[Dict[str, Any]] = []
        total_time = 0.0

        print("🔄 Running automated evaluation...")

        for idx, query in enumerate(self.test_queries, start=1):
            print(f"Processing query {idx}/{len(self.test_queries)}: {query[:50]}...")

            response, response_time = self.evaluate_response_time(query)
            total_time += response_time

            result = {
                "query": query,
                "response": response,
                "response_time": response_time,
                "response_length": len(response),
                "has_response": bool(response.strip()),
                "not_found_response": "couldn't find" in response.lower() or "don't know" in response.lower(),
            }
            results.append(result)

        avg_response_time = total_time / len(self.test_queries)
        success_rate = sum(
            1 for item in results if item["has_response"] and not item["not_found_response"]
        ) / len(results)

        print("\n📊 Automated Evaluation Results:")
        print(f"Average Response Time: {avg_response_time:.2f}s")
        print(f"Success Rate: {success_rate:.1%}")
        print(f"Total Queries Processed: {len(results)}")

        return results

    def save_results(self, results: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Save evaluation results to CSV (and companion JSON)."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_results_{timestamp}.csv"

        output_path = Path(filename)
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        print(f"💾 Results saved to {output_path}")

        json_path = output_path.with_suffix(".json")
        json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"💾 JSON results saved to {json_path}")

        return str(output_path)

    def run_full_evaluation(self, include_manual: bool = False) -> Tuple[List[Dict[str, Any]], str]:
        """Run complete evaluation suite (automated + optional manual)."""
        print("🚀 Academic FAQ Chatbot - Full Evaluation")
        print("=" * 60)

        results = self.automated_evaluation()

        if include_manual:
            print("\n📝 Starting manual relevance evaluation...")
            for item in results[:5]:
                score = self.manual_relevance_score(item["query"], item["response"])
                item["manual_relevance_score"] = score

        filename = self.save_results(results)
        return results, filename


def main() -> None:
    """Entry point for the evaluation script."""
    chatbot = AcademicFAQChatbot()
    evaluator = ChatbotEvaluator(chatbot)

    if not chatbot.is_trained:
        print("❌ Chatbot not trained! Please run knowledge_base_builder.py first.")
        return

    results, filename = evaluator.run_full_evaluation(include_manual=False)

    print(f"\n✅ Evaluation completed! Results saved to {filename}")
    print("💡 Review the results and iterate on your knowledge base if needed.")


if __name__ == "__main__":
    main()
