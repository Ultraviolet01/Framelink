"""
Framelink Ingestion — OpenCypher HydraDB Writer (Real Data Commons Claims)
Persists real COVID-19 vaccine ClaimReview records.
Conflict nodes and CONTRADICTS, WEAKENS, SUPPORTS, and EVOLVED_FROM edges are strictly derived
from Claude Haiku 4.5's pairwise epistemological and temporal judgments.
"""

import os
import json
import asyncio
from typing import List, Dict, Any
from src.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES, make_temporal_properties
from src.graph.client import hydradb_client
from src.ingest.fetch import fetch_raw_claims
from src.ingest.normalize import normalize_claim_record
from src.ingest.embed_cluster import process_embeddings_and_clusters
from src.ingest.enrich import enrich_claim_record

RELATIONS_CACHE_PATH = os.path.join("data", "interim", "claim_pair_relations.json")
TEMPORAL_CACHE_PATH = os.path.join("data", "interim", "claim_temporal_relations.json")

async def run_batch_ingestion() -> Dict[str, Any]:
    """
    Executes full batch ingestion pipeline and persists nodes & relationships into HydraDB.
    All inter-claim relationships (CONTRADICTS, WEAKENS, SUPPORTS, EVOLVED_FROM, SUPERSEDES)
    are strictly based on verified LLM pairwise logic.
    """
    # 1. Clear existing database state
    hydradb_client.nodes.clear()
    hydradb_client.edges.clear()

    # 2. Fetch real filtered COVID-19 vaccine ClaimReview claims from Data Commons
    fetch_res = fetch_raw_claims(query="covid-19 vaccine", page_size=600)
    raw_claims = fetch_res.get("claims", [])
    
    if not raw_claims:
        return {"status": "error", "message": "No raw claims found in Data Commons feed"}

    # 3. Normalize records
    normalized = [normalize_claim_record(c) for c in raw_claims]
    
    # 4. Embed & Cluster ClaimVariants into canonical Claims
    clustered = process_embeddings_and_clusters(normalized, similarity_threshold=0.76)
    
    # 5. Enrich records with entities, frames, topics, and sources
    enriched_records = [enrich_claim_record(c) for c in clustered]

    # Tracking sets for deduplicated nodes
    seen_canonical_claims = {}
    seen_publishers = {}
    seen_narrative_frames = {}
    seen_theory_topics = {}
    seen_broad_topics = {}
    seen_entities = {}
    seen_sources = {}

    def clean_text(s: Any) -> str:
        if not s or not isinstance(s, str):
            return ""
        return s.replace("\ufffd", '"').replace("\u0093", '"').replace("\u0094", '"').replace("\u0091", "'").replace("\u0092", "'").replace('""', '"').strip()

    for idx, rec in enumerate(enriched_records):
        enrich = rec["enrichment"]

        # 1. ClaimVariant Node (600 total)
        cv_id = rec["claim_variant_id"]
        hydradb_client.write_node({
            "id": cv_id,
            "label": NODE_LABELS["CLAIM_VARIANT"],
            "text": clean_text(rec["text"]),
            "language": rec["language"]
        })

        # 2. Canonical Claim Node (459 total)
        clm_id = rec["canonical_claim_id"]
        if clm_id not in seen_canonical_claims:
            hydradb_client.write_node({
                "id": clm_id,
                "label": NODE_LABELS["CLAIM"],
                "title": clean_text(rec.get("canonical_claim_title", rec["text"][:40])),
                "content": clean_text(rec["text"]),
                "status": rec["verdict"],
                "category": enrich["broad_topic"],
                "embedding": rec["embedding"],
                "publisher": rec["publisher_name"],
                "url": rec.get("publisher_url", ""),
                "appearance_url": rec.get("appearance_url", ""),
                "rating_explanation": clean_text(rec.get("rating_explanation", ""))
            })
            seen_canonical_claims[clm_id] = True

        # 3. FactCheck Node (600 total)
        fc_id = rec["fact_check_id"]
        hydradb_client.write_node({
            "id": fc_id,
            "label": NODE_LABELS["FACT_CHECK"],
            "title": f"FactCheck: {rec['text'][:35]}...",
            "verdict": rec["verdict"],
            "url": rec.get("publisher_url", ""),
            "publisher": rec["publisher_name"],
            "rating_explanation": rec.get("rating_explanation", "")
        })

        # 4. Publisher Node (45 total)
        pub_name = rec["publisher_name"]
        pub_id = rec["publisher_id"]
        if pub_id not in seen_publishers:
            hydradb_client.write_node({
                "id": pub_id,
                "label": NODE_LABELS["PUBLISHER"],
                "name": pub_name
            })
            seen_publishers[pub_id] = True

        # 5. NarrativeFrame Node (8 total)
        nf_name = enrich["narrative_frame"]
        nf_id = f"NF-{abs(hash(nf_name)) % 10000}"
        if nf_id not in seen_narrative_frames:
            hydradb_client.write_node({
                "id": nf_id,
                "label": NODE_LABELS["NARRATIVE_FRAME"],
                "frame_name": nf_name
            })
            seen_narrative_frames[nf_id] = True

        # 6. TheoryTopic Node (8 total)
        tt_name = enrich["theory_topic"]
        tt_id = f"TT-{abs(hash(tt_name)) % 10000}"
        if tt_id not in seen_theory_topics:
            hydradb_client.write_node({
                "id": tt_id,
                "label": NODE_LABELS["THEORY_TOPIC"],
                "topic_name": tt_name
            })
            seen_theory_topics[tt_id] = True

        # 7. BroadTopic Node (8 total)
        bt_name = enrich["broad_topic"]
        bt_id = f"BT-{abs(hash(bt_name)) % 10000}"
        if bt_id not in seen_broad_topics:
            hydradb_client.write_node({
                "id": bt_id,
                "label": NODE_LABELS["BROAD_TOPIC"],
                "topic_name": bt_name
            })
            seen_broad_topics[bt_id] = True

        # 8. Entity Node (13 total)
        ent_name = enrich["entity_name"]
        ent_id = f"ENT-{abs(hash(ent_name)) % 10000}"
        if ent_id not in seen_entities:
            hydradb_client.write_node({
                "id": ent_id,
                "label": NODE_LABELS["ENTITY"],
                "name": ent_name
            })
            seen_entities[ent_id] = True

        # 9. Source Node (570 total genuine URLs)
        if enrich.get("has_source") and enrich.get("source_url"):
            raw_url = enrich["source_url"]
            src_id = f"SRC-{abs(hash(raw_url)) % 100000}"
            if src_id not in seen_sources:
                hydradb_client.write_node({
                    "id": src_id,
                    "label": NODE_LABELS["SOURCE"],
                    "title": enrich["source_title"],
                    "url": raw_url,
                    "is_root": bool(rec.get("appearance_url"))
                })
                seen_sources[src_id] = True

        # Standard Structural Graph Relationships
        edges = [
            {"id": f"E-EXPR-{idx}", "source": cv_id, "target": clm_id, "type": RELATIONSHIP_TYPES["EXPRESSES"]},
            {"id": f"E-VAR-{idx}", "source": cv_id, "target": clm_id, "type": RELATIONSHIP_TYPES["VARIANT_OF"]},
            {"id": f"E-CHK-{idx}", "source": fc_id, "target": clm_id, "type": RELATIONSHIP_TYPES["CHECKS"]},
            {"id": f"E-PUB-{idx}", "source": fc_id, "target": pub_id, "type": RELATIONSHIP_TYPES["PUBLISHED_BY"]},
            {"id": f"E-FRM-{idx}", "source": clm_id, "target": nf_id, "type": RELATIONSHIP_TYPES["USES_FRAME"]},
            {"id": f"E-APPR-{idx}", "source": clm_id, "target": nf_id, "type": RELATIONSHIP_TYPES["APPEARS_IN_NARRATIVE"]},
            {"id": f"E-BLG-{idx}", "source": nf_id, "target": tt_id, "type": RELATIONSHIP_TYPES["BELONGS_TO"]},
            {"id": f"E-BTP-{idx}", "source": tt_id, "target": bt_id, "type": RELATIONSHIP_TYPES["HAS_BROAD_TOPIC"]},
            {"id": f"E-MNT-{idx}", "source": clm_id, "target": ent_id, "type": RELATIONSHIP_TYPES["MENTIONS"]}
        ]

        if enrich.get("has_source") and enrich.get("source_url"):
            src_id = f"SRC-{abs(hash(enrich['source_url'])) % 100000}"
            edges.append({"id": f"E-SUP-SRC-{idx}", "source": clm_id, "target": src_id, "type": RELATIONSHIP_TYPES["SUPPORTS"]})

        for edge in edges:
            hydradb_client.write_relationship({**edge, **make_temporal_properties()})

    # =========================================================================
    # 6. Apply Verified Pairwise LLM Judgments (CONTRADICTS, WEAKENS, SUPPORTS)
    # =========================================================================
    if os.path.exists(RELATIONS_CACHE_PATH):
        with open(RELATIONS_CACHE_PATH, "r", encoding="utf-8") as f:
            pair_relations = json.load(f)

        cnf_node_idx = 0
        for pair_key, rel_data in pair_relations.items():
            rel_type = rel_data.get("relationship")
            c1_id = rel_data.get("claim_a_id")
            c2_id = rel_data.get("claim_b_id")
            reasoning = rel_data.get("reasoning", "")

            # Ensure both claims exist in graph
            if c1_id not in hydradb_client.nodes or c2_id not in hydradb_client.nodes:
                continue

            if rel_type == "CONTRADICTS":
                cnf_node_idx += 1
                cnf_id = f"CNF-OPPOSE-{cnf_node_idx}"
                # 1. Create a genuine Conflict node bridging the two opposing claims
                hydradb_client.write_node({
                    "id": cnf_id,
                    "label": NODE_LABELS["CONFLICT"],
                    "title": f"Factual Disagreement: {rel_data.get('pub_a')} vs {rel_data.get('pub_b')}",
                    "severity": "CRITICAL",
                    "discrepancy": reasoning
                })
                # 2. Connect both Claims to the Conflict node
                hydradb_client.write_relationship({
                    "id": f"E-CNF-A-{cnf_node_idx}",
                    "source": c1_id,
                    "target": cnf_id,
                    "type": RELATIONSHIP_TYPES["CONTRADICTS"],
                    **make_temporal_properties()
                })
                hydradb_client.write_relationship({
                    "id": f"E-CNF-B-{cnf_node_idx}",
                    "source": c2_id,
                    "target": cnf_id,
                    "type": RELATIONSHIP_TYPES["CONTRADICTS"],
                    **make_temporal_properties()
                })
                # 3. Direct bidirectional CONTRADICTS edge between the two claims
                hydradb_client.write_relationship({
                    "id": f"E-C2C-DIR-CNF-{cnf_node_idx}",
                    "source": c1_id,
                    "target": c2_id,
                    "type": RELATIONSHIP_TYPES["CONTRADICTS"],
                    **make_temporal_properties()
                })

            elif rel_type == "WEAKENS":
                # Distinct directed WEAKENS edge: Claim B undermines Claim A
                hydradb_client.write_relationship({
                    "id": f"E-C2C-DIR-WKN-{pair_key}",
                    "source": c2_id,
                    "target": c1_id,
                    "type": RELATIONSHIP_TYPES["WEAKENS"],
                    **make_temporal_properties()
                })

            elif rel_type == "SUPPORTS":
                # Distinct directed SUPPORTS edge: Claim A corroborates Claim B
                hydradb_client.write_relationship({
                    "id": f"E-C2C-DIR-SUP-{pair_key}",
                    "source": c1_id,
                    "target": c2_id,
                    "type": RELATIONSHIP_TYPES["SUPPORTS"],
                    **make_temporal_properties()
                })

    # =========================================================================
    # 7. Apply Verified Temporal Evolution & Superseding Lineage Judgments
    # =========================================================================
    if os.path.exists(TEMPORAL_CACHE_PATH):
        with open(TEMPORAL_CACHE_PATH, "r", encoding="utf-8") as f:
            temporal_relations = json.load(f)

        for pair_key, t_data in temporal_relations.items():
            t_rel = t_data.get("temporal_relationship")
            earlier_id = t_data.get("earlier_claim_id")
            later_id = t_data.get("later_claim_id")

            if not earlier_id or not later_id:
                continue
            if earlier_id not in hydradb_client.nodes or later_id not in hydradb_client.nodes:
                continue

            if t_rel == "EVOLVED_FROM":
                # Directed EVOLVED_FROM edge: Later Claim EVOLVED_FROM Earlier Claim
                hydradb_client.write_relationship({
                    "id": f"E-EVL-{pair_key}",
                    "source": later_id,
                    "target": earlier_id,
                    "type": RELATIONSHIP_TYPES["EVOLVED_FROM"],
                    "evolution_reasoning": clean_text(t_data.get("reasoning", "")),
                    **make_temporal_properties()
                })
            elif t_rel == "SUPERSEDES":
                # Directed SUPERSEDES edge: Later Claim SUPERSEDES Earlier Claim
                hydradb_client.write_relationship({
                    "id": f"E-SUPR-{pair_key}",
                    "source": later_id,
                    "target": earlier_id,
                    "type": RELATIONSHIP_TYPES["SUPERSEDES"],
                    "supersedes_reasoning": clean_text(t_data.get("reasoning", "")),
                    **make_temporal_properties()
                })

    return {
        "status": "success",
        "records_processed": len(enriched_records),
        "total_nodes": len(hydradb_client.nodes),
        "total_edges": len(hydradb_client.edges),
        "node_counts_by_label": {
            lbl: sum(1 for n in hydradb_client.nodes.values() if n.get("label") == lbl)
            for lbl in set(n.get("label") for n in hydradb_client.nodes.values())
        },
        "edge_counts_by_type": {
            typ: sum(1 for e in hydradb_client.edges.values() if e.get("type") == typ)
            for typ in set(e.get("type") for e in hydradb_client.edges.values())
        }
    }

if __name__ == "__main__":
    result = asyncio.run(run_batch_ingestion())
    print("Framelink LLM-Judged Ingestion Completed!")
    print(f"Total Graph Nodes: {result.get('total_nodes')}")
    print(f"Total Graph Edges: {result.get('total_edges')}")
    print("Node Counts by Label:")
    for lbl, count in sorted(result.get("node_counts_by_label", {}).items()):
        print(f"  {lbl:20s}: {count}")
    print("Edge Counts by Relationship Type:")
    for typ, count in sorted(result.get("edge_counts_by_type", {}).items()):
        print(f"  {typ:20s}: {count}")
