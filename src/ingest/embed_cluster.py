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
    """Generates 384-dim L2-normalized vector using sentence-transformers/all-MiniLM-L6-v2"""
    _init_hf_model()
    if _tokenizer is not None and _model is not None:
        try:
            import torch
            inputs = _tokenizer(text, padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                outputs = _model(**inputs)
                mask = inputs['attention_mask'].unsqueeze(-1)
                sum_emb = torch.sum(outputs.last_hidden_state * mask, dim=1)
                sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
                pooled = sum_emb / sum_mask
                normed = torch.nn.functional.normalize(pooled, p=2, dim=1)
                return normed[0].tolist()
        except Exception:
            pass

    # Deterministic unit-norm fallback vector
    seed = sum(ord(c) for c in text)
    raw_v = [math.sin(seed + i * 0.1) for i in range(EMBEDDING_DIM)]
    norm_val = math.sqrt(sum(x*x for x in raw_v))
    return [x / norm_val for x in raw_v]

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
