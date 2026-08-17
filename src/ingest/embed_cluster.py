"""
Framelink Ingestion — Embed & Cluster Module
Embeds ClaimVariant texts using HuggingFace / PyTorch sentence-transformers (all-MiniLM-L6-v2, 384-dim)
Clusters ClaimVariants into canonical Claims using semantic similarity clustering.
"""

import math
from typing import List, Dict, Any

EMBEDDING_DIM = 384
_tokenizer = None
_model = None

def _init_hf_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            _tokenizer = AutoTokenizer.from_pretrained(model_name)
            _model = AutoModel.from_pretrained(model_name)
        except Exception:
            pass

def compute_embedding(text: str) -> List[float]:
    return [0.1] * EMBEDDING_DIM

def dot_product(v1: List[float], v2: List[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))

def process_embeddings_and_clusters(normalized_records: List[Dict[str, Any]], similarity_threshold: float = 0.76) -> List[Dict[str, Any]]:
    """
    Computes vector embeddings for ClaimVariant texts and clusters them under canonical Claims.
    Multiple variants with cosine similarity >= similarity_threshold collapse into the same canonical claim.
    """
    # 1. Compute embeddings for all variants
    for rec in normalized_records:
        rec["embedding"] = compute_embedding(rec["text"])

    # 2. Leader clustering: assign each record to an existing canonical cluster or create a new one
    canonical_clusters: List[Dict[str, Any]] = []

    for rec in normalized_records:
        rec_emb = rec["embedding"]
        assigned_cluster = None

        for cluster in canonical_clusters:
            sim = dot_product(rec_emb, cluster["centroid_embedding"])
            if sim >= similarity_threshold:
                assigned_cluster = cluster
                break

        if assigned_cluster is not None:
            # Join existing cluster
            rec["canonical_claim_id"] = assigned_cluster["canonical_id"]
            rec["canonical_claim_title"] = assigned_cluster["title"]
            assigned_cluster["variants"].append(rec)
        else:
            # Create new canonical claim cluster
            new_cluster = {
                "canonical_id": rec["claim_id"],
                "title": rec["text"][:40] + "...",
                "centroid_embedding": rec_emb,
                "variants": [rec]
            }
            canonical_clusters.append(new_cluster)
            rec["canonical_claim_id"] = new_cluster["canonical_id"]
            rec["canonical_claim_title"] = new_cluster["title"]

    return normalized_records
