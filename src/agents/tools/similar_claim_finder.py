"""
Framelink Agent Tool 1 — Similar Claim Finder
Finds semantically similar corporate claims using 384-dim vector embeddings
"""

from typing import List, Dict, Any
from src.retrieval.candidate_gen import find_candidate_claims
from src.ingest.embed_cluster import compute_embedding
from src.graph.client import hydradb_client

async def tool_similar_claim_finder(claim_text: str) -> List[Dict[str, Any]]:
    query_vec = compute_embedding(claim_text)
    all_nodes = list(hydradb_client.nodes.values())
    claims = [n for n in all_nodes if n.get("label") == "Claim"]
    return find_candidate_claims(query_vec, claims, top_k=5, query_text=claim_text)
