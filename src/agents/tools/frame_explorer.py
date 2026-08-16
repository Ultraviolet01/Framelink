"""
Framelink Agent Tool 8 — Frame Explorer
Explores thematic framing categories (ESG, Revenue, Regulatory Compliance)
"""

from typing import Dict, Any
from src.graph.client import hydradb_client

async def tool_frame_explorer(category: str) -> Dict[str, Any]:
    query = f"MATCH (c:Claim {{category: '{category}'}}) RETURN c"
    return await hydradb_client.execute_query(query)
