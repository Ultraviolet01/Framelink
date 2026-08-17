"""
Framelink Universal Parser
Accepts multi-modal payloads (URLs, raw document text, images) from the 9 enterprise sources
(Slack, Gmail, Linear, Google Drive, HubSpot, Fireflies, GitHub, Jira, Confluence).
Parses content, resolves entities, and ingests them into HydraDB.
"""
import time
import urllib.parse
from typing import Dict, Any
from src.graph.client import hydradb_client
from src.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES
from src.ingest.embed_cluster import compute_embedding

# Simple dictionary to simulate OCR / URL fetching for the hackathon demo
MOCK_FETCHERS = {
    "https://github.com/hydra-db/hydradb/issues/42": "The database migration issue is blocking the Apollo feature. Opened by @soham.",
    "mock_image_bytes_123": "OCR Extracted Text: Launch delayed indefinitely due to migration blockers."
}

# Alias resolution mapping
ALIAS_MAP = {
    "@soham": "EMP-001",
    "Sam": "EMP-001",
    "S. Ratnaparkhi": "EMP-001",
    "Alice": "EMP-002"
}

def resolve_author(text: str) -> str:
    """Detects author entity alias from text."""
    for alias, emp_id in ALIAS_MAP.items():
        if alias.lower() in text.lower():
            return emp_id
    return None

def parse_link(url: str, source_system: str) -> str:
    """Parses a web URL (e.g., GitHub issue link)."""
    # For a real implementation, this would use httpx/BeautifulSoup or GitHub API
    return MOCK_FETCHERS.get(url, f"Extracted content from {url}")

def parse_document(text: str) -> str:
    """Parses raw text, markdown, or JSON."""
    return text.strip()

def parse_image(image_bytes: str) -> str:
    """Simulates OCR extraction from an image."""
    return MOCK_FETCHERS.get(image_bytes, "OCR Extraction: Unreadable text")

def ingest_universal_payload(payload_type: str, source_system: str, content: str) -> Dict[str, Any]:
    """
    Main entrypoint: parses the payload and writes it directly to the HydraDB graph substrate.
    """
    if payload_type == "link":
        extracted_text = parse_link(content, source_system)
    elif payload_type == "document":
        extracted_text = parse_document(content)
    elif payload_type == "image":
        extracted_text = parse_image(content)
    else:
        raise ValueError(f"Unsupported payload type: {payload_type}")

    emp_id = resolve_author(extracted_text)
    if emp_id:
        hydradb_client.write_node({
            "id": emp_id,
            "label": NODE_LABELS["ENTITY"],
            "name": f"Resolved Identity: {emp_id}"
        })
    
    import uuid
    # 1. Write ClaimVariant
    cv_id = f"CV-{uuid.uuid4().hex[:8]}"
    hydradb_client.write_node({
        "id": cv_id,
        "label": NODE_LABELS["CLAIM_VARIANT"],
        "text": extracted_text,
        "source_system": source_system
    })

    # 2. Write Publisher (System)
    pub_id = f"PUB-{source_system.upper()}"
    hydradb_client.write_node({
        "id": pub_id,
        "label": NODE_LABELS["PUBLISHER"],
        "name": source_system
    })

    # 3. Write Canonical Claim (simplified clustering for ingestion endpoint)
    clm_id = f"CLM-{uuid.uuid4().hex[:8]}"
    hydradb_client.write_node({
        "id": clm_id,
        "label": NODE_LABELS["CLAIM"],
        "title": f"Extracted {source_system} Fact",
        "content": extracted_text,
        "status": "Pending",
        "category": "Enterprise Data",
        "embedding": compute_embedding(extracted_text),
        "publisher": source_system,
        "url": content if payload_type == "link" else ""
    })

    # Edges
    hydradb_client.write_relationship({
        "id": f"REL-{uuid.uuid4().hex[:8]}",
        "source": cv_id,
        "target": clm_id,
        "type": RELATIONSHIP_TYPES["EXPRESSES"]
    })
    
    hydradb_client.write_relationship({
        "id": f"REL-{uuid.uuid4().hex[:8]}",
        "source": clm_id,
        "target": pub_id,
        "type": RELATIONSHIP_TYPES["PUBLISHED_BY"]
    })

    if emp_id:
        hydradb_client.write_relationship({
            "id": f"REL-{uuid.uuid4().hex[:8]}",
            "source": clm_id,
            "target": emp_id,
            "type": RELATIONSHIP_TYPES["MENTIONS"]
        })

    return {
        "status": "success",
        "ingested_claim_id": clm_id,
        "extracted_text": extracted_text,
        "entity_resolved": emp_id
    }
