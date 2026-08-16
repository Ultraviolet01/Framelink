"""
Framelink Retrieval — 5-Component Weighted Path Ranker Module
Combines similarity + path strength + recency + source trust + conflict density into one weighted composite score with component attribution.
"""

from typing import List, Dict, Any

# Component Weights matching Architecture §5
WEIGHT_SIMILARITY = 0.30
WEIGHT_PATH_STRENGTH = 0.25
WEIGHT_RECENCY = 0.15
WEIGHT_SOURCE_TRUST = 0.20
WEIGHT_CONFLICT_PENALTY = 0.10

def compute_5_component_score(path_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes weighted composite score over 5 components:
    1. Similarity (semantic cosine)
    2. Path Strength (HydraDB graph traversal length & connectivity)
    3. Recency (temporal freshness)
    4. Source Trust (root publisher accreditation)
    5. Conflict Density (contradiction penalty)
    """
    s_sim = path_item.get("candidate_similarity", 0.75)
    s_path = path_item.get("path_strength", 0.85)
    s_rec = path_item.get("recency_score", 0.90)
    s_trust = path_item.get("source_trust", 0.95)
    s_conf = path_item.get("conflict_density", 0.20)  # Contradiction penalty

    composite_score = (
        (WEIGHT_SIMILARITY * s_sim) +
        (WEIGHT_PATH_STRENGTH * s_path) +
        (WEIGHT_RECENCY * s_rec) +
        (WEIGHT_SOURCE_TRUST * s_trust) -
        (WEIGHT_CONFLICT_PENALTY * s_conf)
    )

    composite_score = round(max(min(composite_score, 1.0), 0.0), 4)

    # Component attribution driver identification
    weighted_contribs = {
        "similarity": round(WEIGHT_SIMILARITY * s_sim, 4),
        "path_strength": round(WEIGHT_PATH_STRENGTH * s_path, 4),
        "recency": round(WEIGHT_RECENCY * s_rec, 4),
        "source_trust": round(WEIGHT_SOURCE_TRUST * s_trust, 4),
        "conflict_penalty": round(-WEIGHT_CONFLICT_PENALTY * s_conf, 4)
    }

    dominant_driver = max(
        [("similarity", weighted_contribs["similarity"]),
         ("path_strength", weighted_contribs["path_strength"]),
         ("recency", weighted_contribs["recency"]),
         ("source_trust", weighted_contribs["source_trust"])],
        key=lambda x: x[1]
    )[0]

    return {
        "candidate_id": path_item.get("candidate_id", "CLM-101"),
        "composite_score": composite_score,
        "dominant_driver": dominant_driver,
        "component_breakdown": {
            "similarity_score": s_sim,
            "path_strength": s_path,
            "recency_score": s_rec,
            "source_trust": s_trust,
            "conflict_density": s_conf
        },
        "weighted_contributions": weighted_contribs,
        "attribution_summary": f"Rank score {composite_score:.4f} driven primarily by '{dominant_driver}' (contribution: +{weighted_contribs[dominant_driver]:.4f})."
    }

def rank_expanded_paths(expanded_paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks list of expanded candidate paths using the 5-component weighted formula
    """
    ranked = []
    for item in expanded_paths:
        scored = compute_5_component_score(item)
        ranked.append(scored)

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return ranked
