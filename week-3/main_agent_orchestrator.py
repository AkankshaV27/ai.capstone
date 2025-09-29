import asyncio
from dotenv import load_dotenv

# Import shared modules
from risk_state import CreditRiskState
from agent_clients import RetrievalClient, AnalysisClient 

# LangChain/LangGraph Core Components
from langgraph.graph import StateGraph, START, END
from langchain_core.documents import Document
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode

# --- 1. CONFIGURATION AND INITIALIZATION ---

load_dotenv()

# Setup paths and models (NOTE: FAISS is now handled within the Retrieval Server)
FAISS_INDEX_PATH = "faiss_credit_index"
DOCS_DIR = "mock_documents" 

# Initialize external service clients
RETRIEVAL_CLIENT = RetrievalClient() 
ANALYSIS_CLIENT = AnalysisClient() 
MCP_CLIENT = MultiServerMCPClient({
    "financial-tools-mcp": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
    }
})


# --- 2. LANGGRAPH AGENT NODES (Now implemented via HTTP Calls) ---

async def retrieve_node(state: CreditRiskState) -> dict:
    """Retrieve relevant bank policies from the external Retrieval Agent server."""
    print("--- 🧠 Retrieval Agent: Calling external RAG service (Port 8001)... ---")
    
    try:
        context_data = await RETRIEVAL_CLIENT.retrieve_context(
            loan_type=state['loan_type'],
            loan_amount=state['loan_amount'],
            question=state['question']
        )
        
        # Convert the serializable dicts back into LangChain Document objects
        retrieved_docs = [
            Document(page_content=d['page_content'], metadata=d['metadata'])
            for d in context_data
        ]
        
        return {"context": retrieved_docs}
    except Exception as e:
        print(f"Retrieval Error: {e}")
        return {"context": [Document(page_content=f"Error retrieving policy: {e}", metadata={"source": "Retrieval Agent Error"})]}


async def analysis_or_tool_agent(state: CreditRiskState) -> dict:
    """
    Calls the external Analysis Agent server to decide the next step (Tool, Human Review, or Finalize).
    """
    print(f"\n--- 🤖 Risk Agent: Calling external Analysis service (Port 8002)... ---")
    
    # Prepare the state for serialization and transmission
    state_for_analysis = {
        "loan_type": state["loan_type"],
        "loan_amount": state["loan_amount"],
        "question": state["question"],
        "context": state["context"],
        "tool_results": state["tool_results"],
        "run_count": state["run_count"]
    }
    
    try:
        response = await ANALYSIS_CLIENT.analyze_state(state_for_analysis)
    except Exception as e:
        print(f"Analysis Agent Error: {e}")
        return {
            "analysis_report": f"Communication failure with Analysis Agent: {e}",
            "risk_score": 99,
            "review_status": "Agent Server Failure, Needs Human Review",
            "run_count": state["run_count"] + 1
        }
        
    # The response contains tool_calls OR analysis/status fields
    # if response.get("tool_calls"):
    #     # LangGraph expects tool_calls to be a list of dictionaries
    #     return {"tool_calls": response["tool_calls"], "run_count": response["run_count"]}
    
    # Final analysis or review decision
    return {
        "analysis_report": response.get("analysis_report", ""),
        "risk_score": response.get("risk_score", 0),
        "review_status": response.get("review_status", "Needs Human Review"),
        "run_count": response["run_count"]
    }

def human_in_the_loop_node(state: CreditRiskState) -> dict:
    """Pauses the workflow and awaits human input for high-risk cases."""
    print(f"\n--- 🧑 HUMAN INTERRUPT: Loan {state['request_id']} requires human sign-off! ---")
    
    print(f"Risk Score: {state['risk_score']}")
    print(f"Agent Report: {state['analysis_report']}")
    print(f"Tool History: {state['tool_results']}")
    
    print("Action options: [A]pprove | [R]eject | [T]ool_Call_Missing (Re-run Agent) | [E]xit")
    human_decision = input("Enter decision: ").strip().lower()
    
    if human_decision == 'a':
        return {"review_status": "Human Approved", "human_feedback": "Analyst manually approved risk."}
    elif human_decision == 'r':
        return {"review_status": "Human Rejected", "human_feedback": "Analyst rejected loan due to high risk."}
    elif human_decision == 't':
        return {"review_status": "Needs Rethink/Tool Call", "human_feedback": "Analyst requested re-evaluation with missing data or a new tool call."}
    else:
        return {"review_status": "Workflow Interrupted by Human", "human_feedback": "Human exited the process."}


# --- 3. LANGGRAPH DEFINITION AND EXECUTION ---

async def build_workflow():
    """Defines and compiles the multi-agent LangGraph workflow."""
    workflow = StateGraph(CreditRiskState)

    # Note: All nodes must be async since they involve external calls or are downstream of async nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("analysis_or_tool", analysis_or_tool_agent)
    workflow.add_node("human_review", human_in_the_loop_node)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "analysis_or_tool")

    def route_analysis(state: CreditRiskState) -> str:
        if "Human Review" in state.get("review_status", ""):
            return "human_review"
        elif "Complete" in state.get("review_status", "") or "Approved" in state.get("review_status", ""):
            return END
        return "human_review"

    workflow.add_conditional_edges("analysis_or_tool", route_analysis)

    def route_human_review(state: CreditRiskState) -> str:
        if "Rethink" in state["review_status"]:
            return "analysis_or_tool"
        return END

    workflow.add_conditional_edges("human_review", route_human_review)

    app = workflow.compile()
    print("\nLangGraph Workflow compiled successfully.")
    return app

async def run_workflow(app, initial_state: CreditRiskState):
    """Executes the workflow asynchronously and prints the final outcome."""
    
    print("\n" + "="*50)
    print(f"STARTING LOAN REQUEST: {initial_state['request_id']}")
    print("="*50)

    final_state = initial_state
    
    # We use await for the async stream
    async for step in app.astream(initial_state):
        if step:
            node_name = list(step.keys())[0]
            print(f"\n[STEP COMPLETED] -> {node_name}")
            final_state.update(step[node_name])
            
    print("\n" + "="*50)
    print("WORKFLOW COMPLETE")
    print("="*50)
    print(f"Request ID: {final_state['request_id']}")
    print(f"Risk Score: {final_state.get('risk_score', 'N/A')}")
    print(f"Final Status: {final_state['review_status']}")
    print(f"Final Report: {final_state.get('analysis_report', 'N/A')}")
    print(f"Human Notes: {final_state['human_feedback']}")
    print("="*50)

if __name__ == "__main__":
    
    app = asyncio.run(build_workflow())

    # --- SCENARIO 1: High Risk Loan requiring Tool Call and Human Review ---
    loan_state_1 = {
        "request_id": "L-9001",
        "loan_type": "Unsecured Personal",
        "loan_amount": 600000.00,
        "question": "The applicant has $2500 in monthly debt and $5000 in monthly income. What is their DTI and is this loan approved under policy?",
        "context": [],
        "tool_calls": [],
        "tool_results": [],
        "analysis_report": "",
        "risk_score": 0,
        "review_status": "New Request",
        "human_feedback": "",
        "run_count": 1
    }
    
    # Run the async workflow
    asyncio.run(run_workflow(app, loan_state_1))

    # --- SCENARIO 2: Low Risk Loan (Should be Auto-Approved) ---
    print("\n\n" + "#"*70)
    print("Starting new scenario: Low Risk Loan (Auto-Approved Expected)")
    print("#"*70)
    
    loan_state_2 = {
        "request_id": "L-1002",
        "loan_type": "Mortgage",
        "loan_amount": 250000.00,
        "question": "Loan is below $500k threshold. DTI is confirmed at 30%. Can the agent auto-approve this?",
        "context": [],
        "tool_calls": [],
        "tool_results": [],
        "analysis_report": "",
        "risk_score": 0,
        "review_status": "New Request",
        "human_feedback": "",
        "run_count": 1 
    }
    
    # Run the async workflow
    asyncio.run(run_workflow(app, loan_state_2))
