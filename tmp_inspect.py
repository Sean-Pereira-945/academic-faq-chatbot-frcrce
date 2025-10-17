from semantic_search import SemanticSearchEngine

engine = SemanticSearchEngine()
engine.load_index("models/academic_faq")

query = "When do classes start?"
results = engine.search(query, top_k=5)
print("Semantic results:\n")
for item in results:
    print(item["score"], item["metadata"].get("source"), item["text"][:200])

lex = engine.keyword_search(query, max_results=5)
print("\nLexical results:\n")
for item in lex:
    print(item["score"], item["metadata"].get("source"), item["text"][:200])
