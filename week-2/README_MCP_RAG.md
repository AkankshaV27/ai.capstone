# 📘 README — MCP Financial Tools + RAG Chatbot (Gemini, FAISS, Cohere)

This project combines two components:

1. **MCP Tool Server** → provides financial tools (like DTI calculation and collateral valuation) that can be called by other programs.  
2. **MCP Client (RAG Chatbot)** → reads policy documents, performs hybrid retrieval (semantic + keyword), and uses **Gemini** + **Cohere Re-ranking** + **MCP Tools** to answer user questions.

---

## 🧠 What happens overall

- The **server** is like a *toolbox robot* that knows how to calculate things such as DTI (Debt-to-Income) or estimate collateral value.  
- The **client** is like a *smart chatbot* that reads a document, finds relevant information, and—if needed—calls those tools to help answer questions.

When both run together:

1. The **server** listens locally at `http://127.0.0.1:8000/mcp`.  
2. The **client** connects to that address, retrieves document context, and talks to **Gemini** to reason and respond.

---

## 🧩 Project Structure

```
project/
├─ .env
├─ data/
│  └─ bank_credit_policy.txt
├─ mcp_server.py
└─ mcp_client.py
```

---

## 🔐 Environment Setup

### 1️⃣ Create a `.env` file
Add your API keys:

```
GEMINI_API_KEY=your_google_gemini_api_key
COHERE_API_KEY=your_cohere_api_key
```

---

### 2️⃣ Install dependencies

Use a fresh virtual environment for clean setup.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -U pip
pip install fastmcp langchain langchain-community langchain-google-genai langchain-huggingface langchain-cohere langchain-mcp-adapters langgraph python-dotenv faiss-cpu sentence-transformers rank-bm25 cohere
```

---

### 3️⃣ Prepare data

Create a folder and a text file:
```bash
mkdir -p data
echo "This document explains the bank credit policy and risk management details..." > data/bank_credit_policy.txt
```

---

## ▶️ Running the Project

### 🧮 Step 1 — Start the MCP server

In Terminal #1, run:
```bash
python mcp_server.py
```

✅ Expected output:
```
FastMCP Server running at http://127.0.0.1:8000
```

This means your server is ready with two tools:
- `calculate_dti`
- `get_collateral_valuation`

---

### 💬 Step 2 — Start the RAG Chatbot (client)

In **another terminal window (Terminal #2)**:
```bash
python mcp_client.py
```

You’ll see:
```
--- Week 2: MCP client & RAG with document loader ---
Ask me questions about risk management. Type 'exit' to quit.
You:
```

Now you can chat!

---

### 💡 Example Questions to Try

1. **Document Q&A**
   ```
   You: What does the bank credit policy mention about risk limits?
   ```

2. **Using the DTI tool**
   ```
   You: Calculate DTI for monthly debt 2500 and gross income 6000
   ```

3. **Using the collateral valuation tool**
   ```
   You: Get collateral valuation for asset ID HOME-7731
   ```

4. **Exit**
   ```
   You: exit
   ```

---

## 🧩 How It Works Internally

| Stage | What happens | Technology used |
|-------|---------------|-----------------|
| Document Loading | Reads `bank_credit_policy.txt` and splits it into overlapping chunks. | `RecursiveCharacterTextSplitter` |
| Embedding | Converts text into numeric vectors for meaning. | `HuggingFaceEmbeddings (MiniLM-L6-v2)` |
| Indexing | Stores vectors for semantic search. | `FAISS` |
| Keyword Search | Creates a keyword-based retriever. | `BM25Retriever` |
| Ensemble | Combines both semantic & keyword scores. | `EnsembleRetriever` |
| Reranking | Reorders top results for best relevance. | `CohereRerank` |
| MCP Client | Connects to local tool server. | `MultiServerMCPClient` |
| Gemini Agent | Uses ReAct agent with Gemini + tools. | `ChatGoogleGenerativeAI` via `create_react_agent` |

---

## 🧠 Machine Thought Process

> “I’ll read the policy document and store its meaning.  
> When the user asks a question, I’ll find the most relevant chunks.  
> I’ll use Gemini to think and respond.  
> If the question involves numbers or assets, I’ll call my MCP tools (DTI or valuation) to help me compute before replying.”

---

## 🧰 Troubleshooting

| Issue | Cause | Fix |
|--------|-------|-----|
| Missing API keys | `.env` not loaded | Add GEMINI_API_KEY & COHERE_API_KEY and restart terminal |
| No tools found | Server not running | Start `mcp_server.py` first |
| Blank AI output | LangGraph version mismatch | Fine, can tweak message filter later |
| FAISS install error | Pip outdated | `pip install -U pip faiss-cpu` |
| Slow run | Embedding model downloading | Happens once, cached after |

---

## 🧭 Quick Command Recap

```bash
# Setup venv
python -m venv .venv
source .venv/bin/activate
pip install -U pip

# Install packages
pip install fastmcp langchain langchain-community langchain-google-genai langchain-huggingface langchain-cohere langchain-mcp-adapters langgraph python-dotenv faiss-cpu sentence-transformers rank-bm25 cohere

# Add .env file
# Create data/bank_credit_policy.txt

# Run server
python mcp_server.py

# Run client
python mcp_client.py
```

---

## ✨ Summary

| Component | Role |
|------------|------|
| MCP Server | Provides financial tools (DTI, valuation) |
| MCP Client | Chatbot that retrieves + reasons + uses tools |
| FAISS + BM25 | Hybrid document search |
| Cohere Rerank | Boosts relevance |
| Gemini | Language model that answers |
| LangGraph | Agent framework for ReAct behavior |
