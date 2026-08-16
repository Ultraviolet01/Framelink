"""
Framelink Agent Tool 3 — Related Claims Via Frame & Entity
Finds claims linked to the same entity or thematic frame
"""

from typing import Dict, Any
from src.graph.client import hydradb_client
from src.graph.queries import ENTITY_BRIDGE_QUERY

async def tool_related_claims_via_frame_entity(entity_name: str) -> Dict[str, Any]:
    return await hydradb_client.execute_query(ENTITY_BRIDGE_QUERY, {"entity_name": entity_name})
