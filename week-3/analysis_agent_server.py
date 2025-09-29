import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_mcp_adapters.client import MultiServerMCPClient  # Import MultiServerMCPClient
import uvicorn

# --- CONFIGURATION ---
load_dotenv()

# Initialize MCP client
mcp_client = MultiServerMCPClient({
    "financial-tools-mcp": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
    }
})

# Initialize LLM with tools
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0
)

app = FastAPI(title="Analysis Agent Service")

class AnalysisRequest(BaseModel):
    """Schema for the incoming state from the Orchestrator."""
    loan_type: str
    loan_amount: float
    question: str
    context: List[Dict[str, Any]]
    tool_results: List[str]
    run_count: int

class AnalysisResponse(BaseModel):
    """Schema for the outgoing response to the Orchestrator."""
    tool_calls: List[Dict[str, Any]] = []  # Empty list if no tool call
    analysis_report: str = ""
    risk_score: int = 0
    review_status: str = ""
    run_count: int

# Structured output schema for the final report
analysis_report_schema = {
    "type": "object",
    "properties": {
        "analysis_report": {"type": "string", "description": "A concise summary of the risk findings and policy compliance."},
        "risk_score": {"type": "integer", "description": "The final preliminary risk score (1-100)."},
        "review_status": {"type": "string", "description": "Final status: 'Auto Approved', 'Needs Human Review', or 'Final Analysis Complete'."}
    },
    "required": ["analysis_report", "risk_score", "review_status"]
}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_risk(request: AnalysisRequest):
    """
    Endpoint for the LLM agent to analyze the current state and return analysis.
    """
    # Fetch tools from MCP client
    tools = await mcp_client.get_tools()
    LLM_WITH_TOOLS = LLM.bind_tools(tools)

    print(f"\n--- 🤖 Risk Agent (Run #{request.run_count}): Performing analysis... ---")

    # Reconstruct context string from serializable input
    context_str = "\n---\n".join([doc["page_content"] for doc in request.context])
    tool_results_str = "\n---\n".join(request.tool_results)

    system_prompt = f"""
    You are a Credit Risk Review Agent. Your task is to analyze a loan request and policy compliance.

    Loan Type: {request.loan_type} | Amount: ${request.loan_amount:,.2f}
    Analyst Query: {request.question}

    --- KNOWLEDGE BASE (Bank Policies) ---
    {context_str}

    --- PREVIOUS TOOL RESULTS (MCP Calculations) ---
    {tool_results_str if tool_results_str else 'No tool calls executed yet.'}

    Based on the information, decide the next action:
    1. If a financial calculation (like DTI or valuation) is critically needed, call the appropriate tool defined in your function list.
    2. If all information is available (RAG context and tool results), perform the risk analysis and output the final structured JSON (AnalysisReport).
    3. If the risk is clearly high according to policy (e.g., loan > $500k OR DTI > 40%), or if a key piece of information is still missing, set the review_status to 'Needs Human Review'.

    If providing the AnalysisReport, ensure the risk_score is between 1 (Low) and 100 (High).
    """

    # Invoke LLM with tools
    response = await LLM_WITH_TOOLS.ainvoke(system_prompt)

    # Case 1: Tool call requested
    if response.tool_calls:
        print(f"Agent requested {len(response.tool_calls)} tool call(s).")
        # Format tool calls for immediate return to Orchestrator
        return AnalysisResponse(
            tool_calls=[dict(c) for c in response.tool_calls],
            run_count=request.run_count + 1
        )

    # Case 2: Final analysis or human review requested
    try:
        print(response.content)
        final_report = JsonOutputParser(pydantic_schema=analysis_report_schema).parse(response.content)
        print("Agent completed final analysis.", final_report)
        return AnalysisResponse(
            analysis_report=final_report["analysis_report"],
            risk_score=max(1, min(100, final_report["risk_score"])),
            review_status=final_report["review_status"],
            run_count=request.run_count + 1
        )
    except Exception as e:
        print(f"Agent failed to produce structured output or tool call. Forcing Human Review. Error: {e}")
        return AnalysisResponse(
            analysis_report=response.content,
            risk_score=50,
            review_status="Agent Parse Failure, Needs Human Review",
            run_count=request.run_count + 1
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
