"""
Framelink Retrieval — Candidate Generation & Multi-Hop Expansion Module
Pulls stored embeddings, runs cosine similarity, and expands top candidates via HydraDB algo.MSpaths/SSpaths
"""

import re
import math
import asyncio
from typing import List, Dict, Any
from src.graph.client import hydradb_client
from src.graph.queries import SSPATHS_QUERY, MSPATHS_QUERY
from src.ingest.embed_cluster import compute_embedding

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

def lexical_overlap(query_text: str, target_text: str) -> float:
    if not query_text or not target_text:
        return 0.0
    stop = {"how", "did", "the", "into", "that", "not", "and", "for", "with", "from", "what", "who", "which", "shouldn", "should", "does", "about", "says", "were"}
    q_words = set(w.lower() for w in re.findall(r"\b\w+\b", query_text) if len(w) > 2) - stop
    if not q_words:
        return 0.0
    t_words = set(w.lower() for w in re.findall(r"\b\w+\b", target_text) if len(w) > 2)
    matched = q_words.intersection(t_words)
    return len(matched) / len(q_words)

GENERIC_TERMS = {
    "covid", "vaccine", "vaccination", "vaccines", "coronavirus", "shot", "shots", 
    "people", "would", "recommends", "said", "says", "claim", "claims", "are", 
    "is", "was", "were", "the", "and", "for", "with", "that", "not", "have", "has", "had",
    "do", "does", "did", "of", "in", "to", "on", "about", "a", "an", "or", "but", "this",
    "by", "at", "from", "their", "will", "than", "be"
}

def get_distinctive_overlap_count(query_text: str, target_text: str) -> int:
    if not query_text or not target_text:
        return 0
    q_words = set(re.findall(r"\b\w+\b", query_text.lower())) - GENERIC_TERMS
    t_words = set(re.findall(r"\b\w+\b", target_text.lower())) - GENERIC_TERMS
    matched = q_words.intersection(t_words)
    return len(matched)

def find_candidate_claims(query_vec: List[float], candidates: List[Dict[str, Any]], top_k: int = 5, query_text: str = "") -> List[Dict[str, Any]]:
    """
    Hybrid semantic (dense cosine similarity) + lexical token overlap over candidate claims
    """
    scored = []
    for cand in candidates:
        emb = cand.get("embedding")
        if emb:
            d_sim = cosine_similarity(query_vec, emb)
            l_sim = 0.0
            if query_text:
                cand_text = cand.get("content") or cand.get("title", "")
                l_sim = lexical_overlap(query_text, cand_text)
                final_score = 0.85 * d_sim + 0.15 * l_sim
                overlap_cnt = get_distinctive_overlap_count(query_text, cand_text)
                if overlap_cnt == 1 and d_sim < 0.70:
                    final_score = 0.0
            else:
                final_score = d_sim
            scored.append({
                "id": cand.get("id"),
                "node": cand,
                "similarity_score": round(final_score, 4),
                "dense_score": round(d_sim, 4),
                "lexical_score": round(l_sim, 4)
            })
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_k]

async def generate_candidates_and_expand(query_text: str, top_n: int = 3) -> Dict[str, Any]:
    """
    1. Computes query embedding via all-MiniLM-L6-v2.
    2. Pulls stored embeddings via HydraDB query, brute-forces cosine similarity.
    3. Returns top-N candidate node IDs.
    4. Hands candidates to HydraDB for constrained multi-hop expansion (2-4 hops) via OpenCypher / algo.MSpaths / algo.SSpaths.
    """
    query_embedding = compute_embedding(query_text)
    
    # Query stored nodes from HydraDB
    nodes_res = await hydradb_client.execute_query("MATCH (n) RETURN n")
    all_nodes = nodes_res.get("nodes", list(hydradb_client.nodes.values()))

    # Brute-force hybrid similarity over stored embeddings
    candidate_scores = []
    for node in all_nodes:
        emb = node.get("embedding")
        if emb:
            d_sim = cosine_similarity(query_embedding, emb)
            l_sim = lexical_overlap(query_text, node.get("content", node.get("title", "")))
            final_sim = 0.85 * d_sim + 0.15 * l_sim
            overlap_cnt = get_distinctive_overlap_count(query_text, node.get("content", node.get("title", "")))
            if overlap_cnt == 1 and d_sim < 0.70:
                final_sim = 0.0
            candidate_scores.append({
                "node_id": node["id"],
                "node": node,
                "similarity_score": round(final_sim, 4)
            })

    candidate_scores.sort(key=lambda x: x["similarity_score"], reverse=True)
    top_candidates = candidate_scores[:top_n]
    candidate_ids = [c["node_id"] for c in top_candidates]

    # Hand candidates to HydraDB for multi-hop expansion (2-4 hops) via algo.SSpaths / algo.MSpaths
    expanded_paths = []
    for cand_id in candidate_ids:
        algo_res = await hydradb_client.execute_query(SSPATHS_QUERY, {"start_node_id": cand_id})
        expanded_paths.append({
            "candidate_id": cand_id,
            "candidate_similarity": next((c["similarity_score"] for c in top_candidates if c["node_id"] == cand_id), 0.75),
            "traversal_result": algo_res
        })

    return {
        "query_text": query_text,
        "query_embedding_dim": len(query_embedding),
        "top_candidates": top_candidates,
        "expanded_paths": expanded_paths
    }
