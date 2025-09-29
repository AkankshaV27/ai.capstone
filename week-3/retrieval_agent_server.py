import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
import uvicorn

# --- CONFIGURATION ---
load_dotenv()
FAISS_INDEX_PATH = "faiss_credit_index"
DOCS_DIR = "data"

app = FastAPI(title="Retrieval Agent Service")

class RetrievalRequest(BaseModel):
    """Schema for the incoming request from the Orchestrator."""
    loan_type: str
    loan_amount: float
    question: str

class RetrievalResponse(BaseModel):
    """Schema for the outgoing response to the Orchestrator."""
    context: List[Dict[str, Any]]

# --- RAG KNOWLEDGE BASE SETUP ---

def setup_rag_knowledge_base():
    """Loads mock documents and ensures the FAISS index exists."""
    try:
        print(f"Creating FAISS vector store...")
        os.makedirs(DOCS_DIR, exist_ok=True)
        mock_policy_path = os.path.join(DOCS_DIR, "bank_credit_policy.txt")

        if not os.path.exists(mock_policy_path):
            raise FileNotFoundError(f"The file '{mock_policy_path}' was not found.")

        documents = [Document(page_content=open(mock_policy_path, 'r').read(),
                              metadata={"source": "bank_credit_policy.txt"})]

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        if not os.path.exists(FAISS_INDEX_PATH):
            vectorstore = FAISS.from_documents(texts, embeddings)
            vectorstore.save_local(FAISS_INDEX_PATH)
            print(f"FAISS index saved to {FAISS_INDEX_PATH}/")

        # Load existing FAISS index
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

        cohere_api_key = os.environ.get("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable not set.")

        faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        bm25_retriever = BM25Retriever.from_documents(texts)
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],
            weights=[0.5, 0.5]
        )
        compressor = CohereRerank(model="rerank-v3.5")
        return ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=ensemble_retriever
        )

    except Exception as e:
        print(f"Error setting up RAG knowledge base: {e}")
        return None

@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_policy_context(request: RetrievalRequest):
    """
    Endpoint to retrieve relevant policy documents using RAG.
    """
    print("--- 🧠 Retrieval Agent: Executing RAG search... ---")
    retriever = setup_rag_knowledge_base()

    if not retriever:
        context_data = [
            {"page_content": "Policy documents unavailable. Proceed with caution.", "metadata": {"source": "N/A"}}
        ]
        return RetrievalResponse(context=context_data)

    search_query = f"{request.loan_type} loan for ${request.loan_amount:,.2f}. Question: {request.question}"
    retrieved_docs = retriever.get_relevant_documents(search_query)

    # Convert LangChain Documents to a serializable list of dicts
    context_data = [
        {"page_content": doc.page_content, "metadata": doc.metadata}
        for doc in retrieved_docs
    ]

    return RetrievalResponse(context=context_data)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
