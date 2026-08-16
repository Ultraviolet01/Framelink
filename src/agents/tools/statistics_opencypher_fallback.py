"""
Framelink Agent Tool 9 — Statistics OpenCypher Fallback
Executes raw OpenCypher statistical metrics queries against HydraDB
"""

from typing import Dict, Any
from src.graph.client import hydradb_client

async def tool_statistics_opencypher_fallback(custom_query: str) -> Dict[str, Any]:
    return await hydradb_client.execute_query(custom_query)
