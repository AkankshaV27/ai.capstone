import httpx
import json
from typing import Dict, Any, List

class AgentClient:
    """Base client for all external agent/tool services."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic asynchronous POST request helper."""
        url = self.base_url + endpoint
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", f"HTTP {e.response.status_code} error.")
            print(f"[CLIENT ERROR] Status: {e.response.status_code}, Detail: {error_detail}")
            raise RuntimeError(f"Server error at {self.base_url}{endpoint}: {error_detail}")
        except httpx.RequestError as e:
            print(f"[CLIENT ERROR] Network/Request Error: Could not connect to server at {self.base_url}. Is it running?")
            raise RuntimeError(f"Network error connecting to {self.base_url}{endpoint}: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during POST: {str(e)}")

class RetrievalClient(AgentClient):
    """Client for the Retrieval Agent Service (Port 8001)."""
    
    def __init__(self):
        super().__init__("http://127.0.0.1:8001")

    async def retrieve_context(self, loan_type: str, loan_amount: float, question: str) -> List[Dict[str, Any]]:
        """Calls the Retrieval Agent to get policy documents."""
        data = {
            "loan_type": loan_type,
            "loan_amount": loan_amount,
            "question": question
        }
        response = await self.post("/retrieve", data)
        return response.get("context", [])

class AnalysisClient(AgentClient):
    """Client for the Analysis Agent Service (Port 8002)."""
    
    def __init__(self):
        super().__init__("http://127.0.0.1:8002")

    async def analyze_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calls the Analysis Agent for LLM reasoning/tool selection."""
        # Ensure context is in serializable dict format
        serializable_context = [
            {"page_content": d.page_content, "metadata": d.metadata} 
            for d in state.get("context", [])
        ]
        
        data = {
            "loan_type": state["loan_type"],
            "loan_amount": state["loan_amount"],
            "question": state["question"],
            "context": serializable_context,
            "tool_results": state["tool_results"],
            "run_count": state["run_count"]
        }
        
        return await self.post("/analyze", data)

# class MCPClient(AgentClient):
#     """Client for the MCP Financial Tools Server (Port 8000)."""
    
#     def __init__(self):
#         super().__init__("http://127.0.0.1:8000")
#         self.tool_map = {
#             "calculate_debt_to_income_ratio": "/calculate-dti",
#             "get_collateral_valuation": "/get-collateral-valuation",
#         }
#         mcp_client = MultiServerMCPClient({
#             "financial-tools-mcp": {
#                 "url": "http://127.0.0.1:8000/mcp",
#                 "transport": "streamable_http",
#             }
#         })
#         tools = mcp_client.get_tools()

#     async def execute_tool(self, tool_name: str, args: dict) -> str:
#         """Executes a financial tool by making an asynchronous POST request to the MCP server."""
#         endpoint = self.tool_map.get(tool_name)
#         if not endpoint:
#             return json.dumps({"error": f"Tool '{tool_name}' not found on MCP client map."})

#         try:
#             result_data = await self.post(endpoint, args)
#             # The tool executor expects a stringified JSON output
#             return json.dumps(result_data) 
#         except RuntimeError as e:
#             return json.dumps({"error": str(e)})
