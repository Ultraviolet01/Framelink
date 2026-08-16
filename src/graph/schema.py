"""
Framelink — v3 Schema Definitions & Constants
Contains all 10 Node Labels, 14 Relationship Types, and Temporal Metadata Properties
"""

import time
from typing import Dict, Any

# 10 Node Labels
NODE_LABELS = {
    "CLAIM_VARIANT": "ClaimVariant",
    "CLAIM": "Claim",
    "FACT_CHECK": "FactCheck",
    "PUBLISHER": "Publisher",
    "NARRATIVE_FRAME": "NarrativeFrame",
    "THEORY_TOPIC": "TheoryTopic",
    "BROAD_TOPIC": "BroadTopic",
    "ENTITY": "Entity",
    "SOURCE": "Source",
    "CONFLICT": "Conflict"  # Dedicated Conflict Node
}

# 14 Relationship Types
RELATIONSHIP_TYPES = {
    "EXPRESSES": "EXPRESSES",
    "CHECKS": "CHECKS",
    "PUBLISHED_BY": "PUBLISHED_BY",
    "USES_FRAME": "USES_FRAME",
    "BELONGS_TO": "BELONGS_TO",
    "HAS_BROAD_TOPIC": "HAS_BROAD_TOPIC",
    "MENTIONS": "MENTIONS",
    "VARIANT_OF": "VARIANT_OF",
    "EVOLVED_FROM": "EVOLVED_FROM",
    "SUPERSEDES": "SUPERSEDES",
    "CONTRADICTS": "CONTRADICTS",
    "SUPPORTS": "SUPPORTS",
    "WEAKENS": "WEAKENS",
    "APPEARS_IN_NARRATIVE": "APPEARS_IN_NARRATIVE"
}

def make_temporal_properties(valid_from: str = "2025-01-01T00:00:00Z", valid_to: str = "2099-12-31T23:59:59Z") -> Dict[str, str]:
    """Generates standard temporal property metadata for relationship edges"""
    return {
        "valid_from": valid_from,
        "valid_to": valid_to,
        "transaction_time": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
