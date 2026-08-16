"""
Framelink Retrieval — Threshold Abstention Engine
Triggers explicit abstention responses naming specific conflicting nodes and edges when confidence is low or contradictions exist.
"""

from typing import Dict, Any, List

CONFIDENCE_THRESHOLD = 0.45

def evaluate_abstention(top_path_score: float, conflict_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates whether the fact-checking engine should abstain from picking a side.
    Names specific conflicting nodes and edges if abstaining due to unresolved contradictions.
    """
    # 1. Low Confidence Abstention
    if top_path_score < CONFIDENCE_THRESHOLD:
        return {
            "abstain": True,
            "verdict": "ABSTAIN_LOW_CONFIDENCE",
            "reason": f"Top path composite score ({top_path_score:.4f}) is below confidence threshold ({CONFIDENCE_THRESHOLD}).",
            "named_conflicting_nodes": [],
            "named_conflicting_edges": [],
            "explanation": f"Abstaining from verdict: overall composite score ({top_path_score:.4f}) insufficient for conclusive verification."
        }

    # 2. High Conflict Density Abstention (Contradictions without resolution)
    if conflict_items and len(conflict_items) > 0:
        conflicting_nodes = []
        conflicting_edges = []

        for cnf in conflict_items:
            src_node = cnf.get("source_node", {})
            tgt_node = cnf.get("target_node", {})
            edge = cnf.get("edge", {})

            if src_node:
                conflicting_nodes.append({
                    "id": src_node.get("id"),
                    "label": src_node.get("label"),
                    "title": src_node.get("title") or src_node.get("name")
                })
            if tgt_node:
                conflicting_nodes.append({
                    "id": tgt_node.get("id"),
                    "label": tgt_node.get("label"),
                    "title": tgt_node.get("title") or tgt_node.get("name")
                })
            if edge:
                conflicting_edges.append({
                    "id": edge.get("id"),
                    "type": edge.get("type"),
                    "severity": cnf.get("severity", "HIGH"),
                    "discrepancy": cnf.get("discrepancy", "Factual Contradiction")
                })

        node_names_str = ", ".join([f"[{n.get('id')}] '{n.get('title')}'" for n in conflicting_nodes[:2]])
        edge_names_str = ", ".join([f"[{e.get('id')}] {e.get('type')}" for e in conflicting_edges[:2]])

        return {
            "abstain": True,
            "verdict": "ABSTAIN_CONTRADICTORY_EVIDENCE",
            "reason": f"Active contradictory evidence detected between {node_names_str} linked via {edge_names_str}.",
            "named_conflicting_nodes": conflicting_nodes,
            "named_conflicting_edges": conflicting_edges,
            "explanation": f"Explicit Abstention: Fact-checker detected unresolved contradiction between {node_names_str} via edge {edge_names_str}. Refusing to pick a side without primary audit resolution."
        }

    # 3. No Abstention Required
    return {
        "abstain": False,
        "verdict": "VERIFIED_CORROBORATED",
        "reason": f"Top path composite score ({top_path_score:.4f}) exceeds threshold with no unresolved conflicts.",
        "named_conflicting_nodes": [],
        "named_conflicting_edges": [],
        "explanation": "Claim successfully corroborated against HydraDB context graph."
    }
