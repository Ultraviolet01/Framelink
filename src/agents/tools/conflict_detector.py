"""
Framelink Agent Tool 5 — Conflict Detector
Executes directional Cypher graph contradiction queries for specific candidate claims,
and uses claude-haiku-4-5-20251001 with prompt caching for live real-time conflict analysis.
"""

import os
import json
from typing import Dict, Any, List, Optional
from src.graph.client import hydradb_client
from src.retrieval.candidate_gen import find_candidate_claims
from src.ingest.embed_cluster import compute_embedding

MODEL = "claude-haiku-4-5-20251001"

CONFLICT_SYSTEM_PROMPT = """You are a real-time conflict evaluation agent for a graph fact-checking engine.
Analyze contradictory evidence pairs, identify discrepancies, and assess severity scores.
Return ONLY valid JSON with keys: severity, discrepancy, resolution_recommendation.
"""

async def tool_conflict_detector(query_text: Optional[str] = None, claim_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Checks for active contradictions and conflicts specifically connected to the queried claims.
    """
    target_claim_ids = set(claim_ids or [])
    
    if query_text and not target_claim_ids:
        qvec = compute_embedding(query_text)
        claims = [n for n in hydradb_client.nodes.values() if n.get("label") == "Claim"]
        cands = find_candidate_claims(qvec, claims, top_k=1, query_text=query_text)
        target_claim_ids = set(c["id"] for c in cands if c.get("similarity_score", 0) >= 0.55)

    if not target_claim_ids:
        return {"status": "success", "conflicts_count": 0, "conflicts": []}

    # Find CONTRADICTS edges touching these target claims
    conflicts_found = []
    for e in hydradb_client.edges.values():
        if e.get("type") == "CONTRADICTS":
            src = e.get("source")
            tgt = e.get("target")
            if src in target_claim_ids or tgt in target_claim_ids:
                src_node = hydradb_client.nodes.get(src, {})
                tgt_node = hydradb_client.nodes.get(tgt, {})
                conflicts_found.append({
                    "edge_id": e.get("id"),
                    "source_node": src_node,
                    "target_node": tgt_node,
                    "edge": e,
                    "discrepancy": tgt_node.get("discrepancy") or src_node.get("discrepancy") or "Direct contradiction between claims"
                })

    raw_res = {
        "status": "success",
        "conflicts_count": len(conflicts_found),
        "conflicts": conflicts_found
    }

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key and conflicts_found:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            cnf_sample = conflicts_found[0]
            resp = client.messages.create(
                model=MODEL,
                max_tokens=300,
                system=[
                    {
                        "type": "text",
                        "text": CONFLICT_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": f"Conflict Node: {json.dumps(cnf_sample)}"}]
            )
            parsed = json.loads(resp.content[0].text)
            raw_res["llm_conflict_analysis"] = parsed
        except Exception:
            pass

    return raw_res
