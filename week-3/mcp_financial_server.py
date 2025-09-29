# mcp_financial_server_fastmcp.py
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("financial-tools-mcp")

@mcp.tool
def calculate_dti(monthly_debt: float, gross_income: float) -> dict:
    """
    Calculate the Debt-to-Income (DTI) ratio.
    
    Args:
        monthly_debt: Total monthly debt payments.
        gross_income: Gross monthly income.
    
    Returns:
        Dictionary with DTI ratio, risk flag, and summary.
    """
    if gross_income <= 0:
        raise ValueError("Gross income must be positive.")
    
    dti = (monthly_debt / gross_income) * 100
    risk_flag = "High DTI" if dti > 40 else "Acceptable DTI"
    
    return {
        "dti_ratio": round(dti, 2),
        "risk_flag": risk_flag,
        "summary": f"The DTI ratio is {round(dti, 2)}%. This is classified as {risk_flag}."
    }

@mcp.tool
def get_collateral_valuation(asset_id: str) -> dict:
    """
    Fetch the estimated market value of a collateral asset.
    
    Args:
        asset_id: Unique identifier of the asset.
    
    Returns:
        Dictionary with asset_id, valuation, and summary.
    """
    simulated_value = hash(asset_id) % 500000 + 100000
    
    return {
        "asset_id": asset_id,
        "valuation": simulated_value,
        "summary": f"The estimated collateral value for '{asset_id}' is ${simulated_value:,.2f}."
    }

if __name__ == "__main__":
    # Start the MCP server
    mcp.run(transport="http", host="127.0.0.1", port=8000)
