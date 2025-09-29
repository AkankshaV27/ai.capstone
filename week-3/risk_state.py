from typing import TypedDict, List
from langchain_core.documents import Document

# Define the structure for a tool call, which is a dict containing the name and arguments.
# Example: {"name": "calculate_debt_to_income_ratio", "args": {"monthly_debt": 2500, "gross_income": 5000}}
ToolCall = TypedDict("ToolCall", {"name": str, "args": dict})

class CreditRiskState(TypedDict):
    """
    Represents the state of a single loan request as it moves through the multi-agent system.
    This structure is shared by the Orchestrator, Retrieval, and Analysis agents.
    """
    # --- Input Fields ---
    request_id: str
    loan_type: str
    loan_amount: float
    question: str
    
    # --- RAG/Context Fields ---
    context: List[Document] # Retrieved policy documents from RAG
    
    # --- Tool Execution Fields ---
    tool_calls: List[ToolCall] # Tools the LLM recommends calling (set by analysis_or_tool)
    tool_results: List[str] # Results from the executed MCP tools (set by tool_executor_node)

    # --- Agent Output/Status Fields ---
    analysis_report: str # Final summary/rationale from the LLM
    risk_score: int # Calculated risk score (1-100)
    review_status: str # 'New Request', 'Needs Human Review', 'Complete', 'Human Approved', etc.
    human_feedback: str # Notes from the human review node
    run_count: int # Simple counter to prevent infinite loops (e.g., failed tool calls)