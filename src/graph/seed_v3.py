"""
Framelink — v3 Schema Graph Seeder
Manually writes 15 fake claims covering 100% of node labels (10/10) and relationship types (14/14) with embeddings and temporal metadata
"""

from src.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES, make_temporal_properties
from src.graph.client import hydradb_client
from src.ingest.embed_cluster import compute_embedding

def seed_v3_graph():
    """
    Populates HydraDB substrate with v3 schema graph
    """
    # Clear existing state
    hydradb_client.nodes.clear()
    hydradb_client.edges.clear()

    # --- 10 NODE LABELS (15 Nodes Total) ---
    nodes = [
        # 1. ClaimVariant
        {"id": "CV-101", "label": NODE_LABELS["CLAIM_VARIANT"], "text": "Acme Corp 100% Net Zero in 2025 (Social Post Variant)", "lang": "en", "embedding": compute_embedding("Acme Corp 100% Net Zero in 2025")},
        {"id": "CV-102", "label": NODE_LABELS["CLAIM_VARIANT"], "text": "OmniTech Revenue Surge 45% YoY (Earnings Call Variant)", "lang": "en", "embedding": compute_embedding("OmniTech Revenue Surge 45% YoY")},
        
        # 2. Claim
        {"id": "CLM-101", "label": NODE_LABELS["CLAIM"], "title": "Acme Net-Zero FY2025", "content": "Acme Corporation achieved 100% Net-Zero carbon emissions across all global facilities in FY2025.", "status": "CONTRADICTED", "entity": "Acme Corporation", "embedding": compute_embedding("Acme Corporation achieved 100% Net-Zero carbon emissions across all global facilities in FY2025.")},
        {"id": "CLM-102", "label": NODE_LABELS["CLAIM"], "title": "OmniTech Q3 Revenue Surge", "content": "OmniTech Cloud Services generated $3.2B revenue representing 45% YoY growth.", "status": "REFUTED", "entity": "OmniTech Solutions Inc.", "embedding": compute_embedding("OmniTech Cloud Services generated $3.2B revenue representing 45% YoY growth.")},
        {"id": "CLM-103", "label": NODE_LABELS["CLAIM"], "title": "Acme Carbon Baseline 2024", "content": "Acme Corporation baseline emissions for 2024 was 150,000 MT CO2e.", "status": "SUPERSEDED", "entity": "Acme Corporation", "embedding": compute_embedding("Acme Corporation baseline emissions for 2024 was 150,000 MT CO2e.")},

        # 3. FactCheck
        {"id": "FC-201", "label": NODE_LABELS["FACT_CHECK"], "title": "Fact-Check: Acme Net-Zero Claims Audited", "verdict": "FALSE", "rating_score": 0.15},

        # 4. Publisher
        {"id": "PUB-201", "label": NODE_LABELS["PUBLISHER"], "name": "Global ESG FactCheck Organization", "domain": "factcheck.org"},

        # 5. NarrativeFrame
        {"id": "NF-301", "label": NODE_LABELS["NARRATIVE_FRAME"], "frame_name": "Corporate Greenwashing & Carbon Offsets"},

        # 6. TheoryTopic
        {"id": "TT-401", "label": NODE_LABELS["THEORY_TOPIC"], "topic_name": "Environmental Accounting & Offset Auditing"},

        # 7. BroadTopic
        {"id": "BT-401", "label": NODE_LABELS["BROAD_TOPIC"], "topic_name": "Sustainability & Climate Policy"},

        # 8. Entity
        {"id": "ENT-501", "label": NODE_LABELS["ENTITY"], "name": "Acme Corporation", "ticker": "ACME"},
        {"id": "ENT-502", "label": NODE_LABELS["ENTITY"], "name": "US Environmental Protection Agency", "ticker": "EPA"},

        # 9. Source
        {"id": "SRC-501", "label": NODE_LABELS["SOURCE"], "title": "EPA Clean Air Sentinel Satellite Registry #TX-99", "url": "https://epa.gov/sentinel/tx-99", "is_root": True},

        # 10. Conflict Node (Dedicated Node)
        {"id": "CNF-301", "label": NODE_LABELS["CONFLICT"], "title": "Methane Flaring vs Net-Zero Offsets Contradiction", "severity": "CRITICAL", "discrepancy": "Un-offset 42,000 MT methane flaring detected"}
    ]

    for n in nodes:
        hydradb_client.write_node(n)

    # --- 14 RELATIONSHIP TYPES WITH TEMPORAL PROPERTIES ---
    edges = [
        {"id": "EDG-01", "source": "CV-101", "target": "CLM-101", "type": RELATIONSHIP_TYPES["EXPRESSES"], **make_temporal_properties()},
        {"id": "EDG-02", "source": "CV-102", "target": "CV-101", "type": RELATIONSHIP_TYPES["VARIANT_OF"], **make_temporal_properties()},
        {"id": "EDG-03", "source": "FC-201", "target": "CLM-101", "type": RELATIONSHIP_TYPES["CHECKS"], **make_temporal_properties()},
        {"id": "EDG-04", "source": "FC-201", "target": "PUB-201", "type": RELATIONSHIP_TYPES["PUBLISHED_BY"], **make_temporal_properties()},
        {"id": "EDG-05", "source": "CLM-101", "target": "NF-301", "type": RELATIONSHIP_TYPES["USES_FRAME"], **make_temporal_properties()},
        {"id": "EDG-06", "source": "NF-301", "target": "TT-401", "type": RELATIONSHIP_TYPES["BELONGS_TO"], **make_temporal_properties()},
        {"id": "EDG-07", "source": "TT-401", "target": "BT-401", "type": RELATIONSHIP_TYPES["HAS_BROAD_TOPIC"], **make_temporal_properties()},
        {"id": "EDG-08", "source": "CLM-101", "target": "ENT-501", "type": RELATIONSHIP_TYPES["MENTIONS"], **make_temporal_properties()},
        {"id": "EDG-09", "source": "CLM-101", "target": "CLM-103", "type": RELATIONSHIP_TYPES["EVOLVED_FROM"], **make_temporal_properties()},
        {"id": "EDG-10", "source": "CLM-101", "target": "CLM-103", "type": RELATIONSHIP_TYPES["SUPERSEDES"], **make_temporal_properties()},
        {"id": "EDG-11", "source": "CLM-101", "target": "CNF-301", "type": RELATIONSHIP_TYPES["CONTRADICTS"], **make_temporal_properties()},
        {"id": "EDG-12", "source": "CNF-301", "target": "SRC-501", "type": RELATIONSHIP_TYPES["SUPPORTS"], **make_temporal_properties()},
        {"id": "EDG-13", "source": "CNF-301", "target": "CLM-101", "type": RELATIONSHIP_TYPES["WEAKENS"], **make_temporal_properties()},
        {"id": "EDG-14", "source": "CLM-102", "target": "NF-301", "type": RELATIONSHIP_TYPES["APPEARS_IN_NARRATIVE"], **make_temporal_properties()}
    ]

    for e in edges:
        hydradb_client.write_relationship(e)

    return {
        "nodes_written": len(hydradb_client.nodes),
        "edges_written": len(hydradb_client.edges)
    }
