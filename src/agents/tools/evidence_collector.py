"""
Framelink Agent Tool 4 — Evidence Collector
Collects supporting, refuting, and audit evidence nodes linked to a claim
"""

from typing import Dict, Any
from src.graph.client import hydradb_client

async def tool_evidence_collector(claim_id: str) -> Dict[str, Any]:
    query = f"MATCH (c:Claim {{id: '{claim_id}'}})<-[r:SUPPORTS|REFUTES|VERIFIED_BY]-(e:Evidence) RETURN c, r, e"
    return await hydradb_client.execute_query(query)
