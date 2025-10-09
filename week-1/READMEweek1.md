# Week 1–2 Capstone: PDF QA Chatbot with Hybrid Search, Ensemble Retrieval, and Re‑ranking (As‑Is)

This README explains your script **exactly as written** and gives **step‑by‑step run instructions**.

## Overview (what it does)
- Loads a PDF
- Splits it into overlapping chunks
- Builds **FAISS** (semantic) and **BM25** (keyword) search
- **Ensemble blends** both results (50/50)
- **Cohere Rerank** reorders candidates by relevance
- **Gemini** answers using the retrieved chunks (via LangChain’s `RetrievalQA`)
- Appends **source page numbers** used

## Project structure (expected)
```
your-project/
├─ data/
│  └─ Johnson_H.pdf
└─ week-1/
   └─ rag.py
```

## Environment variables (.env)
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_key_here
COHERE_API_KEY=your_cohere_key_here
```

## Install dependencies
```bash
# optional venv
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows powershell
# .venv\Scripts\Activate.ps1

pip install -U pip
pip install langchain-google-genai python-dotenv pypdf faiss-cpu sentence-transformers cohere rank-bm25

# if imports fail for some langchain parts:
pip install langchain langchain-community
```

## Run
1) Ensure `data/Johnson_H.pdf` exists.  
2) Ensure `.env` has valid keys.  
3) Start:
```bash
python week-1/rag.py
```
4) Ask questions (type `exit` to quit).

## Troubleshooting
- **PDF not found** or **unpack error after load_documents** → Check `data/Johnson_H.pdf` path.
- **`GEMINI_API_KEY ... not set`** → Add it to `.env`.
- **Cohere rerank error** → Add `COHERE_API_KEY` and ensure `rerank-v3.5` access.
- **FAISS install issues** → Use `faiss-cpu` and a clean venv.
- **`PyPDFLoader` import error** → Your code uses `from langchain.document_loaders import PyPDFLoader`. If it fails with your LangChain version, install `langchain-community` and (only if you choose to modify code) switch the import to `from langchain_community.document_loaders import PyPDFLoader`.

## Why this works (intuition)
- **BM25** finds exact words → great for names/codes.
- **FAISS** understands meaning → great for paraphrases.
- **Ensemble** improves recall; **Rerank** improves precision.
- **RetrievalQA** keeps Gemini grounded to your PDF and shows **source pages**.
