import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_cohere import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

DOCS_DIR = "data"
load_dotenv()

def load_documents():
    print(f"Creating FAISS vector store...")
    os.makedirs(DOCS_DIR, exist_ok=True)
    mock_policy_path = os.path.join(DOCS_DIR, "bank_credit_policy.txt") 
    documents = [Document(page_content=open(mock_policy_path, 'r').read(),
                          metadata={"source": "bank_credit_policy.txt"})]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    faiss_vectorstore = FAISS.from_documents(texts, embeddings)

    return (faiss_vectorstore, texts)

def create_retriever(faiss_vectorstore, texts):
    cohere_api_key = os.environ.get("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY environment variable not set.")

    faiss_retriever = faiss_vectorstore.as_retriever()
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

async def get_llm_response(question, retriever, mcp_client):
    retrieved_docs = retriever.invoke(question)
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    tools = await mcp_client.get_tools()

    agent = create_react_agent(
        tools=tools,
        model=ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.environ.get("GEMINI_API_KEY"),
            temperature=0
        )
    )

    full_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    raw_response = await agent.ainvoke({"messages": [{"role": "user", "content": full_prompt}]})
                                       
    messages = raw_response.get("messages", [])
    final_texts = []

    for msg in messages:
        # AIMessage with normal content
        if isinstance(msg, AIMessage) and msg.content.strip():
            final_texts.append(msg.content.strip())

    return "\n".join(final_texts)

async def main():
    print("--- Week 2: MCP client & RAG with document loader ---")
    print("Ask me questions about risk management. Type 'exit' to quit.")

    vectorstore, texts = load_documents()
    retriever = create_retriever(vectorstore, texts)

    mcp_client = MultiServerMCPClient({
        "financial-tools-mcp": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
        }
    })

    while True:
        user_query = input("You: ")
        if user_query.lower() == "exit":
            break
        bot_response = await get_llm_response(user_query, retriever, mcp_client)
        print("Bot:", bot_response)

if __name__ == "__main__":
    asyncio.run(main())