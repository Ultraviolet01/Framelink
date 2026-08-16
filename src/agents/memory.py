"""
Framelink Agent — HydraDB Memory Substrate Module
Writes intermediate reasoning steps, query history, and session state back into HydraDB as short-term/long-term memory nodes.
"""

import time
from typing import Dict, Any
from src.graph.client import hydradb_client
from src.graph.schema import make_temporal_properties

def save_session_memory(session_id: str, query_text: str, planner_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persists session state and intermediate reasoning nodes into HydraDB graph substrate
    """
    mem_node_id = f"MEM-{session_id}-{int(time.time()*1000)}"
    
    memory_node = {
        "id": mem_node_id,
        "label": "SessionMemory",
        "session_id": session_id,
        "query": query_text,
        "verdict": planner_result.get("verdict", "PENDING"),
        "tools_triggered": planner_result.get("tools_triggered", []),
        "critic_audit_passed": planner_result.get("critic_audit", {}).get("passed", True),
        **make_temporal_properties()
    }
    
    hydradb_client.write_node(memory_node)

    # Link memory node to claim target if present
    target_claim_id = "CLM-101"
    hydradb_client.write_relationship({
        "id": f"REL-MEM-{mem_node_id}",
        "source": mem_node_id,
        "target": target_claim_id,
        "type": "AUDITED_BY_SESSION",
        **make_temporal_properties()
    })

    return {
        "memory_node_id": mem_node_id,
        "session_id": session_id,
        "status": "PERSISTED_TO_HYDRADB"
    }
