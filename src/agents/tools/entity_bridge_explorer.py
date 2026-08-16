"""
Framelink Agent Tool 7 — Entity Bridge Explorer
Explores corporate connections and shared vendors linking distinct claims
"""

from typing import Dict, Any
from src.graph.client import hydradb_client

async def tool_entity_bridge_explorer(entity1: str, entity2: str) -> Dict[str, Any]:
    query = f"MATCH p = shortestPath((e1:Entity {{name: '{entity1}'}})-[*]-(e2:Entity {{name: '{entity2}'}})) RETURN p"
    return await hydradb_client.execute_query(query)
