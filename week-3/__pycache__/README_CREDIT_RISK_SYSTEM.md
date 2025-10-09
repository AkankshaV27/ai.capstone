# 🧠 Multi‑Agent Credit Risk Analysis System (MCP + RAG + Gemini + LangGraph)

This repository implements a **multi‑agent AI system** designed to perform **credit‑risk assessment** using document retrieval, reasoning, and external financial tools.  
It’s built with **LangChain**, **LangGraph**, and **FastAPI**, connecting multiple microservices that cooperate intelligently.

---

## 🚀 Overview of Components

| Component | Description | Port |
|------------|--------------|------|
| 🧮 `mcp_financial_server.py` | Hosts **financial tools** such as DTI (Debt‑to‑Income) and collateral valuation via **FastMCP**. | `8000` |
| 📚 `retrieval_agent_server.py` | Loads credit policy docs, builds **FAISS + BM25 hybrid retriever**, and exposes an API for RAG context. | `8001` |
| 🧠 `analysis_agent_server.py` | Runs a **Gemini LLM + Cohere ReRank** pipeline, connecting to MCP tools to reason and compute results. | `8002` |
| 🔗 `main_agent_orchestrator.py` | Coordinates the workflow — retrieval → analysis → optional human review → decision. | — |
| 🤝 `agent_clients.py` | Contains HTTP/MCP clients to communicate across services. | — |
| 🧾 `risk_state.py` | Defines the shared state (TypedDict) exchanged between workflow steps. | — |

---

## 🧩 How the System Thinks (Machine Perspective)

1. **The MCP Server** provides “hands” — external tools like *calculate DTI* and *get asset valuation*.
2. **The Retrieval Agent** acts like a memory librarian — it finds relevant text snippets from policy documents.
3. **The Analysis Agent** is the “brain” — it uses Gemini and the MCP tools to analyze borrower data and produce a risk report.
4. **The Orchestrator** is the manager — it decides which agent should act next, handles retries, and gathers final results.

---

## ⚙️ Setup & Installation

### 1️⃣ Create a Virtual Environment
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

### 2️⃣ Install Dependencies
```bash
pip install -U pip
pip install fastapi uvicorn httpx python-dotenv
pip install langchain langchain-community langchain-google-genai langchain-huggingface langchain-cohere langgraph
pip install sentence-transformers faiss-cpu rank-bm25 cohere fastmcp langchain-mcp-adapters
```

### 3️⃣ Set Environment Variables
Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_key_here
COHERE_API_KEY=your_cohere_key_here
```

### 4️⃣ Prepare the Data Folder
Create a text file for your policy corpus:
```bash
mkdir -p data
echo "This document explains the bank credit policy and risk management rules..." > data/bank_credit_policy.txt
```

---

## ▶️ Run the System (4 Terminals)

### 🧮 Terminal 1 — MCP Financial Server
```bash
python mcp_financial_server.py
```
Runs at → **http://127.0.0.1:8000/mcp**  
Provides financial tools (DTI & Collateral Valuation).

---

### 📚 Terminal 2 — Retrieval Agent Server
```bash
python retrieval_agent_server.py
```
Loads the policy text, builds FAISS index, combines BM25+FAISS, re‑ranks using Cohere, and serves `/retrieve`.  
Runs at → **http://127.0.0.1:8001**

---

### 🧠 Terminal 3 — Analysis Agent Server
```bash
python analysis_agent_server.py
```
Connects to MCP tools and Gemini. Accepts inputs and outputs structured credit‑risk analysis.  
Runs at → **http://127.0.0.1:8002**

---

### 🔗 Terminal 4 — Main Orchestrator
```bash
python main_agent_orchestrator.py
```
Calls retrieval → analysis → optional tool executions → human review → final report.

---

## 🧪 Example Queries

```
What does the credit policy say about risk limits?
Calculate DTI for monthly debt 2500 and gross income 6000.
Estimate collateral valuation for asset ID HOME-9981.
Summarize overall credit risk for a borrower with high DTI and low collateral.
```

---

## 🧭 Architecture Overview

```
User → Orchestrator
        ├─> Retrieval Agent (BM25 + FAISS → Cohere Rerank)
        ├─> Analysis Agent (Gemini + MCP Tools)
        │        └─> MCP Financial Tools (DTI / Valuation)
        └─> Human Review (optional)
→ Final Structured Credit Risk Report
```

---

## ✅ Quick Command Summary

| Step | Command | Purpose |
|------|----------|----------|
| 1 | `python mcp_financial_server.py` | Start financial tools |
| 2 | `python retrieval_agent_server.py` | Serve retrieval results |
| 3 | `python analysis_agent_server.py` | Run analysis + reasoning |
| 4 | `python main_agent_orchestrator.py` | Run full workflow |

---

## 🧯 Troubleshooting

| Problem | Likely Cause | Fix |
|----------|---------------|------|
| `KeyError: GEMINI_API_KEY` | `.env` missing or invalid | Check `.env` path and key names |
| Empty retrieval results | Missing `bank_credit_policy.txt` | Ensure the file exists and is not empty |
| FAISS import fails | Incompatible wheel | `pip install faiss-cpu` |
| Connection refused | Port conflict | Check that ports 8000–8002 are free |
| Slow first run | Embeddings downloading | Only occurs once; cached afterward |

---

## 🌟 Congratulations

You’ve now built a modular **AI multi‑agent ecosystem**:  
- **Memory** → Retrieval Agent  
- **Reasoning** → Analysis Agent  
- **Action** → MCP Server Tools  
- **Control** → Orchestrator  

Together, they perform a full credit‑risk evaluation pipeline! 🚀
