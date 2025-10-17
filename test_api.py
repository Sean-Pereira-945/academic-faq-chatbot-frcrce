"""Quick test to check if chatbot is working."""
from chatbot import AcademicFAQChatbot

print("Testing chatbot initialization...")
bot = AcademicFAQChatbot()

print(f"Is trained: {bot.is_trained}")
print(f"Embedding backend: {bot.search_engine.embedding_backend}")

if bot.is_trained:
    print("\n✅ Knowledge base is loaded!")
    print("\nTesting a question...")
    response = bot.generate_response("What is the academic calendar?")
    print(f"\nResponse:\n{response}")
else:
    print("\n❌ Knowledge base NOT loaded!")
    print("\nChecking files...")
    import os
    faiss_exists = os.path.exists("models/academic_faq.faiss")
    pkl_exists = os.path.exists("models/academic_faq_data.pkl")
    print(f"FAISS file exists: {faiss_exists}")
    print(f"PKL file exists: {pkl_exists}")
