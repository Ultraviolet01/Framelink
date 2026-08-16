"""
Framelink API — REST Endpoints Router
Core query endpoint (/api/v1/query) plus structured lookups (/claims/{id}, /entities/{id}, /conflicts)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from src.graph.client import hydradb_client
from src.agents.planner import execute_dynamic_planner
from src.admin.metrics import get_system_metrics

router = APIRouter(prefix="/api/v1", tags=["REST API"])

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "SESS-REST-01"

@router.post("/query")
async def api_query(req: QueryRequest):
    """Executes dynamic agent planner query across HydraDB graph substrate"""
    if not req.query:
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    if len(hydradb_client.nodes) == 0:
        from src.ingest.write_graph import run_batch_ingestion
        await run_batch_ingestion()
    return await execute_dynamic_planner(req.query, session_id=req.session_id)

@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    """Structured lookup: Claim node by ID"""
    node = hydradb_client.nodes.get(claim_id)
    if not node:
        # Search case-insensitive
        for n in hydradb_client.nodes.values():
            if n.get("id", "").lower() == claim_id.lower():
                node = n
                break
    if not node:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found")
    return node

@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Structured lookup: Entity node by ID"""
    node = hydradb_client.nodes.get(entity_id)
    if not node:
        for n in hydradb_client.nodes.values():
            if n.get("id", "").lower() == entity_id.lower() or n.get("name", "").lower() == entity_id.lower():
                node = n
                break
    if not node:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
    return node

@router.get("/conflicts")
async def get_conflicts():
    """Lists active conflict nodes and contradiction edges"""
    res = await hydradb_client.execute_query("MATCH (c1)-[r:CONTRADICTS]-(c2) RETURN c1, r, c2")
    return {
        "conflicts_count": len(res.get("conflicts", [])),
        "conflicts": res.get("conflicts", [])
    }

@router.get("/metrics")
async def get_metrics():
    """Returns real-time graph inspection metrics"""
    return get_system_metrics()
