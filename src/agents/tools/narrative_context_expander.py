"""
Framelink Agent Tool 2 — Narrative Context Expander
Expands claim context across multi-hop graph paths in HydraDB
"""

from typing import Dict, Any
from src.graph.client import hydradb_client
from src.graph.queries import MULTI_HOP_TRAVERSAL_QUERY

async def tool_narrative_context_expander(claim_id: str) -> Dict[str, Any]:
    return await hydradb_client.execute_query(MULTI_HOP_TRAVERSAL_QUERY, {"claim_id": claim_id})
