#!/usr/bin/env python3
"""Knowledge base builder for the Academic FAQ Chatbot."""

import argparse
import os
from typing import Iterable, List

from chatbot import AcademicFAQChatbot
from data_processor import DocumentProcessor
from semantic_search import SemanticSearchEngine


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the knowledge base and optionally answer questions from PDFs.",
    )
    parser.add_argument(
        "--pdf-dir",
        default="data/pdfs",
        help="Directory containing PDF documents to ingest (default: data/pdfs)",
    )
    parser.add_argument(
        "--urls-file",
        default="data/urls.txt",
        help="Optional URLs file to ingest alongside PDFs (default: data/urls.txt)",
    )
    parser.add_argument(
        "--skip-urls",
        action="store_true",
        help="Skip ingesting URLs and only use PDFs when building the knowledge base.",
    )
    parser.add_argument(
        "-q",
        "--question",
        action="append",
        help="Question to answer using the freshly built knowledge base. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--questions-file",
        help="Path to a text file containing one question per line to answer after building the knowledge base.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enter an interactive Q&A loop after building the knowledge base.",
    )
    parser.add_argument(
        "--embedding-backend",
        choices=["sbert", "gemini"],
        default="gemini",
        help="Embedding backend to use for semantic indexing (default: gemini).",
    )
    return parser.parse_args()


def _collect_questions(args: argparse.Namespace) -> List[str]:
    questions: List[str] = []
    if args.question:
        questions.extend(q.strip() for q in args.question if q and q.strip())

    if args.questions_file:
        try:
            with open(args.questions_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    cleaned = line.strip()
                    if cleaned:
                        questions.append(cleaned)
        except FileNotFoundError:
            print(f"⚠️  Questions file not found: {args.questions_file}")

    # Remove duplicates while preserving order
    seen = set()
    unique_questions: List[str] = []
    for question in questions:
        if question not in seen:
            unique_questions.append(question)
            seen.add(question)

    return unique_questions


def _ensure_urls_placeholder(urls_file: str) -> None:
    if os.path.exists(urls_file):
        return

    os.makedirs(os.path.dirname(urls_file) or ".", exist_ok=True)
    with open(urls_file, "w", encoding="utf-8") as file:
        file.write("# Add your university URLs here, one per line\n")
        file.write("# Example:\n")
        file.write("# https://university.edu/faq\n")
        file.write("# https://university.edu/academic-calendar\n")
    print(f"📝 Created {urls_file} - please add your URLs there")


def _answer_questions(bot: AcademicFAQChatbot, questions: Iterable[str]) -> None:
    for question in questions:
        print("\n❓ Question:", question)
        answer = bot.generate_response(question)
        print("\n" + answer + "\n")


def _interactive_loop(bot: AcademicFAQChatbot) -> None:
    print("\n🤖 Entering interactive mode. Type 'exit' or press Ctrl+C to stop.\n")
    try:
        while True:
            question = input("You: ").strip()
            if not question or question.lower() in {"exit", "quit", "q"}:
                print("👋 Exiting interactive mode.")
                break
            answer = bot.generate_response(question)
            print("\n" + answer + "\n")
    except KeyboardInterrupt:
        print("\n👋 Exiting interactive mode.")


def main():
    """Entry point for building the semantic knowledge base."""
    args = _parse_arguments()
    print("🚀 Academic FAQ Chatbot - Knowledge Base Builder")
    print("=" * 60)

    # Initialize components
    processor = DocumentProcessor()
    search_engine = SemanticSearchEngine(embedding_backend=args.embedding_backend)

    # Create URLs file if it doesn't exist
    urls_file = None if args.skip_urls else args.urls_file
    if urls_file:
        _ensure_urls_placeholder(urls_file)

    # Process all documents
    print("📚 Processing documents...")
    all_chunks = processor.process_all_documents(
        pdf_dir=args.pdf_dir,
        urls_file=urls_file if urls_file else "",
        include_urls=bool(urls_file),
    )

    pdf_url_chunk_count = len(all_chunks)

    if not all_chunks:
        print("❌ No documents found! Please add PDFs to data/pdfs/ or URLs to data/urls.txt")
        return

    if pdf_url_chunk_count:
        print(f"📄 Total chunks extracted: {pdf_url_chunk_count}")
    else:
        print("⚠️  No chunks extracted from PDFs or URLs")

    # Build knowledge base
    search_engine.build_knowledge_base(all_chunks)

    # Save knowledge base
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    search_engine.save_index("models/academic_faq")

    print("✅ Knowledge base building completed!")
    print("📊 Summary:")
    print(f"  - Total text chunks: {len(all_chunks)}")
    print("  - Embedding backend:", search_engine.embedding_backend.upper())
    print("  - Model saved to: models/academic_faq")
    print("  - Ready for Phase 3: Core Application Development")

    pending_questions = _collect_questions(args)
    if pending_questions or args.interactive:
        bot = AcademicFAQChatbot()
        bot.search_engine = search_engine
        bot.is_trained = True

        if pending_questions:
            print("\n🔎 Answering provided questions using PDF-derived knowledge...")
            _answer_questions(bot, pending_questions)

        if args.interactive:
            _interactive_loop(bot)


if __name__ == "__main__":
    main()
