"""
Enterprise Ingestion Pipeline for HydraDB
Simulates processing of noisy, multi-source enterprise data, resolving entity aliases,
and detecting contradictions to build a queryable graph.
"""
import os
import json
import time
from src.graph.client import hydradb_client
from src.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES
from src.ingest.embed_cluster import compute_embedding

ENTERPRISE_DATA_PATH = os.path.join("data", "raw", "enterprise_sample.json")

# Entity resolution mapping (Simulating LLM or AD alias resolution)
ALIAS_MAP = {
    "@soham": "EMP-001",
    "Sam": "EMP-001",
    "S. Ratnaparkhi": "EMP-001",
    "Alice": "EMP-002"
}

EMP_DETAILS = {
    "EMP-001": {"name": "Soham Ratnaparkhi", "role": "Engineer"},
    "EMP-002": {"name": "Alice", "role": "Product Manager"}
}

async def run_enterprise_ingestion():
    # 1. Clear existing database state
    hydradb_client.nodes.clear()
    hydradb_client.edges.clear()

    # 2. Load Enterprise Fixture
    with open(ENTERPRISE_DATA_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    # 3. Create Entities
    for emp_id, details in EMP_DETAILS.items():
        hydradb_client.write_node({
            "id": emp_id,
            "label": NODE_LABELS["ENTITY"],
            "name": details["name"],
            "role": details["role"]
        })

    canonical_claims = {}
    conflict_nodes = []
    
    # 4. Ingest Documents
    for doc in docs:
        if "Lunch" in doc["content"]:
            continue # skip noise

        author_alias = doc.get("author") or doc.get("assignee") or doc.get("last_editor")
        emp_id = ALIAS_MAP.get(author_alias)

        # Write ClaimVariant (raw text chunk)
        cv_id = f"CV-{doc['id']}"
        hydradb_client.write_node({
            "id": cv_id,
            "label": NODE_LABELS["CLAIM_VARIANT"],
            "text": doc["content"],
            "source_system": doc["source_system"]
        })
        
        # Write Publisher (System)
        pub_id = f"PUB-{doc['source_system']}"
        hydradb_client.write_node({
            "id": pub_id,
            "label": NODE_LABELS["PUBLISHER"],
            "name": doc["source_system"]
        })

        # Ontology Alignment: Grouping Slack as "Launch Confirmed" and Jira/Conf as "Launch Delayed"
        if doc["source_system"] == "Slack":
            canonical_id = "CLM-APOLLO-LAUNCH"
            status = "Confirmed"
            category = "Engineering"
        else:
            canonical_id = "CLM-APOLLO-DELAYED"
            status = "Blocked"
            category = "Engineering"

        if canonical_id not in canonical_claims:
            embedding = [0.1] * 384
            clm_node = {
                "id": canonical_id,
                "label": NODE_LABELS["CLAIM"],
                "title": f"Apollo Feature {status}",
                "content": doc["content"],
                "status": status,
                "category": category,
                "embedding": embedding,
                "publisher": doc["source_system"],
                "url": doc["url"]
            }
            hydradb_client.write_node(clm_node)
            canonical_claims[canonical_id] = clm_node

        # Edges
        hydradb_client.write_relationship({
            "source": cv_id,
            "target": canonical_id,
            "type": RELATIONSHIP_TYPES["EXPRESSES"]
        })
        
        hydradb_client.write_relationship({
            "source": canonical_id,
            "target": pub_id,
            "type": RELATIONSHIP_TYPES["PUBLISHED_BY"]
        })

        if emp_id:
            hydradb_client.write_relationship({
                "source": canonical_id,
                "target": emp_id,
                "type": RELATIONSHIP_TYPES["MENTIONS"]
            })

    # 5. Conflict Resolution (Simulating the LLM contradiction output)
    if "CLM-APOLLO-LAUNCH" in canonical_claims and "CLM-APOLLO-DELAYED" in canonical_claims:
        cnf_id = "CNF-APOLLO"
        hydradb_client.write_node({
            "id": cnf_id,
            "label": NODE_LABELS["CONFLICT"],
            "description": "Contradiction regarding the Apollo feature launch date."
        })
        
        hydradb_client.write_relationship({
            "source": "CLM-APOLLO-LAUNCH",
            "target": cnf_id,
            "type": RELATIONSHIP_TYPES["CONTRADICTS"],
            "severity": "HIGH",
            "discrepancy": "Slack claims launching Tuesday, but Jira/Confluence report delayed indefinitely."
        })
        hydradb_client.write_relationship({
            "source": "CLM-APOLLO-DELAYED",
            "target": cnf_id,
            "type": RELATIONSHIP_TYPES["CONTRADICTS"],
            "severity": "HIGH",
            "discrepancy": "System of record (Confluence/Jira) states blocked, contradicting informal Slack chat."
        })

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_enterprise_ingestion())
    print("Enterprise graph populated!")
