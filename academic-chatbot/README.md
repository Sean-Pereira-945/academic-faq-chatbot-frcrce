# Academic FAQ Chatbot 🎓

An end-to-end academic helpdesk assistant built with semantic search, Streamlit, and robust evaluation tooling. Trained on curated university documents, the chatbot gives students instant answers to policy, deadline, and registration questions.

| Phase | Description | Status |
| --- | --- | --- |
| Phase 1 | Environment setup, dependency pinning, project scaffolding | ✅ Completed |
| Phase 2 | Data ingestion, chunking, embedding, FAISS indexing | ✅ Completed |
| Phase 3 | Chatbot core logic, Streamlit UI | ✅ Completed |
| Phase 4 | Automated/manual evaluation suite, smoke + unit tests | ✅ Completed |
| Phase 5 | Documentation, polish, and release prep | ✅ Completed |

---

## 🔍 Key Features

- **Hybrid knowledge base** — ingest PDFs and live web pages with consistent chunking and metadata tracking.
- **Semantic retrieval** — Sentence-Transformers embeddings with a FAISS index deliver fast, high-quality matches.
- **Contextual answers** — Returns the most relevant handbook sentences with inline citations so students see the original source instantly.
- **Optional Gemini summarisation** — With a Google Gemini API key, the assistant asks Gemini to synthesise the retrieved snippets into concise, source-cited summaries tailored to each question.
- **Gemini-powered retrieval (optional)** — Swap the embedding backend to Gemini's `text-embedding-004` model for a deeper semantic understanding of your PDFs.
- **Smart reranking** — Cross-encoder re-ranking plus a lexical fallback ensure low-confidence queries (like "financial aid") still surface the best-matching handbook snippets instead of generic fallbacks.
- **Conversational UX** — Streamlit app with chat history, metrics, and guardrails for greetings and farewells.
- **Evaluation toolkit** — Automated response-time benchmarking, optional manual scoring, and exportable reports.
- **Test coverage** — Unit tests for conversational logic plus a reusable smoke test harness.
- **Compatibility shim** — Seamlessly supports recent `huggingface_hub` releases while honoring the pinned `sentence-transformers` version.

---

## ⚙️ Quickstart

### Prerequisites
- Python 3.10 or newer (project developed on Python 3.13)
- [Git](https://git-scm.com/)
- Recommended: virtual environment tooling (`venv`, `conda`, or `pipenv`)

### 1. Clone and bootstrap
```cmd
git clone <repository-url>
cd academic-chatbot
python -m venv chatbot_env
chatbot_env\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Verify environment & dependencies
```cmd
python test_setup.py
```
This script checks GPU/CPU availability, validates the Hugging Face compatibility shim, and confirms that required directories exist.

### 3. Ingest your academic sources
- Place PDFs under `data/pdfs/` (any depth; the loader walks subdirectories).
- Add seed URLs to `data/urls.txt` (one per line). The builder auto-creates the file with guidance comments if missing.

### 4. Build the knowledge base
```cmd
python knowledge_base_builder.py
```
Outputs:
- `models/academic_faq.faiss` — FAISS index
- `models/academic_faq.pkl` — serialized metadata (embeddings + chunk store)
- Console summary with processed chunk count

Gemini embeddings are now the default. To fall back to the sentence-transformer backend (if you do not have an API key set), run:

```cmd
python knowledge_base_builder.py --embedding-backend sbert
```
Make sure `GEMINI_API_KEY` is set; otherwise the builder automatically falls back to the sentence-transformer backend with a warning.

### 5. Launch the chatbot UI
```cmd
streamlit run app.py
```
Visit the local URL that Streamlit prints (defaults to http://localhost:8501). Use the sidebar to check knowledge-base status, response metrics, and quick tips.

> 💡 _Want Gemini-powered wording?_ Set the `GEMINI_API_KEY` environment variable (see [Gemini integration](#-gemini-integration-optional)) before launching the app.

---

## 🧱 Project Structure
```
academic-chatbot/
├── app.py                     # Streamlit UI entry point
├── chatbot.py                 # Conversational core logic
├── data_processor.py          # PDF + web ingestion and chunking
├── semantic_search.py         # Embedding, FAISS index, compatibility shim
├── knowledge_base_builder.py  # Orchestrates preprocessing + index export
├── evaluate.py                # Automated evaluation pipeline
├── test_suite.py              # End-to-end smoke tests
├── test_setup.py              # Environment verification helper
├── data/
│   ├── pdfs/                  # Drop PDF sources here
│   ├── web_pages/             # Cached HTML snapshots (auto-generated)
│   └── urls.txt               # Seed URLs (created if missing)
├── models/                    # Saved FAISS index + metadata files
├── tests/
│   └── test_chatbot.py        # Unit tests for chatbot behaviour
├── docs/                      # Extended documentation & artifacts
└── requirements.txt           # Pinned dependencies
```

---

## 🧠 Knowledge Base Workflow
1. **Document processing** (`DocumentProcessor`)
	- Normalizes and extracts text from PDFs via `pdfplumber`.
	- Fetches and cleans HTML via `requests` + `BeautifulSoup`.
	- Splits content into overlapping chunks with source metadata.
2. **Embedding & Indexing** (`SemanticSearchEngine`)
	- Uses `sentence-transformers/all-MiniLM-L6-v2` by default (override via constructor).
	- Stores embeddings and chunk metadata alongside a FAISS index.
	- Provides `search(query, top_k)` returning text, score, and metadata.
3. **Persistence**
	- `save_index(path_prefix)` writes both `.faiss` and `.pkl` files.
	- `load_index(path_prefix)` restores the index at chatbot startup.

Customize chunk size, overlap, or model choice by editing constants in `data_processor.py` and `semantic_search.py`.

---

## 💬 Using the Chatbot Programmatically
```python
from chatbot import AcademicFAQChatbot

bot = AcademicFAQChatbot()

if not bot.is_trained:
	 raise RuntimeError("Build the knowledge base first (python knowledge_base_builder.py)")

print(bot.generate_response("How do I register for classes?"))
```
`generate_response` handles greetings, fallbacks, and confidence thresholds automatically. Use `get_stats()` to report chunk counts inside the Streamlit UI or custom dashboards.

---

## 📊 Evaluation & Testing

### Automated benchmarks
```cmd
python evaluate.py
```
- Runs a curated set of academic FAQs.
- Measures response latency, length, and fallback frequency.
- Saves `evaluation_results_YYYYMMDD_HHMMSS.csv` and a matching `.json` in the working directory.
- Pass `include_manual=True` within `run_full_evaluation` to record 1–5 relevance scores for a sample of queries.

### Test suite
```cmd
python -m unittest tests/test_chatbot.py
python test_suite.py
```
- Unit tests validate preprocessing, greeting detection, and high-confidence response formatting.
- `test_suite.py` exercises an end-to-end conversation flow for quick smoke checks.

Consider wiring these commands into CI (GitHub Actions, Azure DevOps, etc.) to ensure each update keeps the knowledge base healthy.

---

## 🔧 Configuration Tips
- **Model overrides**: Instantiate `SemanticSearchEngine(model_name="sentence-transformers/all-mpnet-base-v2")` for higher-quality embeddings (requires more resources).
- **Chunk tuning**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` in `data_processor.py` to match document density.
- **Index location**: Provide a custom path to `save_index`/`load_index` to version multiple knowledge bases (e.g., semester-specific indexes).
- **Proxy / offline mode**: Populate `data/web_pages/` with manually downloaded HTML to avoid outbound network calls; the processor skips fetching if cached files exist.
- **Logging**: Toggle verbose logging in `semantic_search.py` to inspect FAISS operations when debugging.

---

## ✨ Gemini Integration (Optional)

Level up answer fluency by letting Google Gemini rewrite the curated bullet points the chatbot collects. The integration is opt-in and falls back to deterministic formatting if unavailable.

1. Enable the [Google Generative AI](https://ai.google.dev/gemini-api/docs/api-key) API and create an API key.
2. Install dependencies (already included in `requirements.txt`). If you set up earlier, run:

	```cmd
	pip install -r requirements.txt
	```

3. Expose the key in your shell before launching Streamlit or running the bot programmatically:

	```cmd
	set GEMINI_API_KEY=your-api-key-here
	```

	(Use `export` on macOS/Linux shells.)

4. Start the chatbot as usual. When the key is present, Gemini will synthesise the retrieved snippets into a concise, source-cited answer while strictly staying within the retrieved facts. Pair it with the (default) Gemini embedding backend to have Gemini handle both retrieval and final wording.

If the key is missing or the API call fails, the chatbot automatically reverts to its bullet-point presentation, so reliability is unaffected. Similarly, the knowledge-base builder falls back to sentence-transformer embeddings whenever the Gemini API is unavailable, ensuring the pipeline still completes.

---

## 🛠️ Troubleshooting
| Issue | Resolution |
| --- | --- |
| `Academic FAQ Assistant` says the knowledge base isn't built | Run `python knowledge_base_builder.py` and confirm `models/academic_faq.faiss` exists. |
| Streamlit shows `ModuleNotFoundError` | Verify virtual environment activation and rerun `pip install -r requirements.txt`. |
| Hugging Face download failures behind a firewall | Pre-download the model and set the `HF_HOME` environment variable, or copy the `sentence-transformers` model into `models/`. |
| Evaluation script halts waiting for input | Disable manual scoring by keeping `include_manual=False` (default). |
| PDFs produce empty chunks | Check PDF text extraction (scanned PDFs may need OCR). Consider adding Tesseract or requesting text-based versions. |

---

## 🚀 Roadmap & Next Steps
- Expand analytics in the Streamlit sidebar (feedback capture, usage charts).
- Add conversational memory or retrieval-augmented generation (RAG) summarization for multi-turn questions.
- Integrate CI to automate `test_suite.py`, `evaluate.py`, and linting on pull requests.
- Explore multi-tenant deployments (different academic departments or campuses).

Contributions and feedback are welcome! Open an issue or submit a pull request detailing proposed enhancements.

---

## 📚 Resources
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Streamlit](https://streamlit.io/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

---

Happy building! Empower your campus community with instant, trustworthy academic answers. 🎓