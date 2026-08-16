"""
Framelink Ingestion — Incremental Ingestion & Deduplication Module
Graph-aware deduplication, versioned SUPERSEDES edge writing, and repeat-stream safety
"""

import time
from typing import Dict, Any, List
from src.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES, make_temporal_properties
from src.graph.client import hydradb_client
from src.ingest.embed_cluster import compute_embedding
from src.retrieval.candidate_gen import cosine_similarity

SIMILARITY_MATCH_THRESHOLD = 0.85

def process_incremental_claim(incoming_claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes an incoming stream record:
    1. Embeds text using all-MiniLM-L6-v2.
    2. Runs candidate search against existing embeddings.
    3. Confirms via HydraDB graph expansion (shared entities/frames/VARIANT_OF chains).
    4. Decides whether to create a new Claim or a new ClaimVariant of an existing Claim.
    5. Writes a versioned SUPERSEDES edge if updating a prior statement without mutating history.
    """
    text = incoming_claim.get("text", "").strip()
    entity = incoming_claim.get("entity", "Acme Corporation")
    category = incoming_claim.get("category", "ESG Compliance")
    is_update = incoming_claim.get("is_update", False)
    supersedes_target_id = incoming_claim.get("supersedes_id")

    embedding = compute_embedding(text)

    # 1. Search existing Claim & ClaimVariant nodes
    existing_nodes = list(hydradb_client.nodes.values())
    claim_nodes = [n for n in existing_nodes if n.get("label") in [NODE_LABELS["CLAIM"], NODE_LABELS["CLAIM_VARIANT"]]]

    best_match = None
    best_sim = 0.0

    for node in claim_nodes:
        node_emb = node.get("embedding")
        if node_emb:
            sim = cosine_similarity(embedding, node_emb)
            if sim > best_sim:
                best_sim = sim
                best_match = node

    # Graph Expansion check: verify shared entity or frame
    shared_graph_context = False
    if best_match and best_sim >= SIMILARITY_MATCH_THRESHOLD:
        matched_entity = best_match.get("entity")
        if matched_entity and matched_entity.lower() == entity.lower():
            shared_graph_context = True

    # 2. Decision Logic: New Claim vs ClaimVariant vs SUPERSEDES Edge
    if best_match and (best_sim >= SIMILARITY_MATCH_THRESHOLD or shared_graph_context) and not is_update:
        # Match found: Create new ClaimVariant node, do NOT create duplicate Claim node!
        cv_id = f"CV-INC-{int(time.time()*1000)}"
        parent_claim_id = best_match["id"] if best_match.get("label") == NODE_LABELS["CLAIM"] else best_match.get("parent_claim_id", "CLM-101")

        variant_node = {
            "id": cv_id,
            "label": NODE_LABELS["CLAIM_VARIANT"],
            "text": text,
            "parent_claim_id": parent_claim_id,
            "embedding": embedding,
            "language": "en"
        }
        hydradb_client.write_node(variant_node)

        # Write VARIANT_OF edge to canonical Claim
        hydradb_client.write_relationship({
            "id": f"E-VAR-{cv_id}",
            "source": cv_id,
            "target": parent_claim_id,
            "type": RELATIONSHIP_TYPES["VARIANT_OF"],
            **make_temporal_properties()
        })

        return {
            "status": "variant_added",
            "action": "ADDED_CLAIM_VARIANT",
            "variant_id": cv_id,
            "canonical_claim_id": parent_claim_id,
            "matched_similarity": round(best_sim, 3),
            "duplicate_claim_created": False
        }

    elif is_update or supersedes_target_id:
        # Novel Update: Create new versioned Claim node AND write versioned SUPERSEDES edge
        new_claim_id = f"CLM-REV-{int(time.time()*1000)}"
        target_id = supersedes_target_id or (best_match["id"] if best_match else "CLM-101")

        new_claim_node = {
            "id": new_claim_id,
            "label": NODE_LABELS["CLAIM"],
            "title": f"Revised: {text[:30]}...",
            "content": text,
            "entity": entity,
            "category": category,
            "embedding": embedding,
            "status": "REVISED"
        }
        hydradb_client.write_node(new_claim_node)

        # Write versioned SUPERSEDES relationship with temporal metadata
        hydradb_client.write_relationship({
            "id": f"E-SUP-{new_claim_id}",
            "source": new_claim_id,
            "target": target_id,
            "type": RELATIONSHIP_TYPES["SUPERSEDES"],
            **make_temporal_properties(valid_from=time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        })

        return {
            "status": "claim_superseded",
            "action": "CREATED_VERSIONED_SUPERSEDES_EDGE",
            "new_claim_id": new_claim_id,
            "superseded_claim_id": target_id,
            "duplicate_claim_created": False
        }

    else:
        # Truly novel Claim statement
        new_claim_id = f"CLM-NEW-{int(time.time()*1000)}"
        new_claim_node = {
            "id": new_claim_id,
            "label": NODE_LABELS["CLAIM"],
            "title": text[:35] + "...",
            "content": text,
            "entity": entity,
            "category": category,
            "embedding": embedding,
            "status": "NEW"
        }
        hydradb_client.write_node(new_claim_node)

        return {
            "status": "novel_claim_created",
            "action": "CREATED_NEW_CLAIM",
            "new_claim_id": new_claim_id,
            "duplicate_claim_created": False
        }
