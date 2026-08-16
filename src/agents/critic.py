"""
Framelink Agent — Output Review Critic
Audits planner tool outputs before returning: enforces abstention rules, checks grounded proof trails, and catches bad outputs.
"""

from typing import Dict, Any, List

def review_planner_output(planner_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Critic Review Step:
    - Confirms an abstention wasn't skipped when contradictory evidence exists.
    - Confirms returned path is grounded in actual tool outputs.
    - Corrects verdict and injects named conflicting evidence if critic detects un-flagged conflicts.
    """
    result = dict(planner_result)
    tool_outputs = result.get("tool_outputs", {})
    conflicts_found = result.get("conflicts_found", [])

    # Check 1: Audit for un-flagged contradiction conflicts
    if not conflicts_found and "ConflictDetector" in tool_outputs:
        conflicts_found = tool_outputs["ConflictDetector"].get("conflicts", [])

    is_unflagged_conflict = len(conflicts_found) > 0 and result.get("verdict") not in ["ABSTAIN_CONTRADICTORY_EVIDENCE", "CONTRADICTED"]

    if len(conflicts_found) > 0:
        # Critic forces explicit abstention with named conflicting nodes and edges
        conflicting_nodes = []
        conflicting_edges = []
        for cnf in conflicts_found:
            src = cnf.get("source_node", {})
            tgt = cnf.get("target_node", {})
            edge = cnf.get("edge", {})
            if src: conflicting_nodes.append(src.get("id"))
            if tgt: conflicting_nodes.append(tgt.get("id"))
            if edge: conflicting_edges.append(edge.get("type"))

        result["critic_audit"] = {
            "passed": False,
            "reason": "Critic caught un-flagged contradictory evidence. Overriding verdict to explicit abstention.",
            "original_verdict": planner_result.get("verdict"),
            "forced_abstention": True
        }
        # Create plain English explanation
        if not conflicts_found:
            explanation = "I cannot provide a definitive verdict due to conflicting evidence."
            tech_trace = ""
        else:
            # Pick the first conflict to explain
            c = conflicts_found[0]
            src = c.get("source_node", {})
            tgt = c.get("target_node", {})
            
            # Helper to extract text and links
            def get_claim_details(node):
                if node.get("label") == "Conflict":
                    return node.get("discrepancy") or node.get("title", "A conflicting assertion")
                text = node.get("content") or node.get("title", "")
                pub = node.get("publisher", "a fact-checker")
                verdict = node.get("status", "Unverified")
                url = node.get("url", "")
                link = f" [{pub} investigation ↗]({url})" if url else f" ({pub})"
                return f'"{text}" (Verdict: {verdict}{link})'

            src_details = get_claim_details(src)
            tgt_details = get_claim_details(tgt)
            
            explanation = (
                "There are conflicting claims about this topic that prevent a definitive answer.\n\n"
                f"- On one side: {src_details}\n"
                f"- On the other side: {tgt_details}\n\n"
                "Because these verified claims directly contradict each other in the graph, I cannot resolve this automatically and must abstain."
            )
            
            tech_trace = (
                "**Critic Audit Override**\n"
                f"- **Conflicting Nodes**: `{list(set(conflicting_nodes))}`\n"
                f"- **Edge Types**: `{list(set(conflicting_edges))}`\n"
            )

        result["verdict"] = "ABSTAIN_CONTRADICTORY_EVIDENCE"
        result["named_conflicting_nodes"] = list(set(conflicting_nodes))
        result["named_conflicting_edges"] = list(set(conflicting_edges))
        result["explanation"] = explanation
        result["technical_details"] = tech_trace
        return result

    # Check 2: Audit Grounding
    path_explainer_out = tool_outputs.get("PathExplainer", {})
    is_grounded = path_explainer_out.get("is_grounded", True)

    if not is_grounded:
        result["critic_audit"] = {
            "passed": False,
            "reason": "Critic caught un-grounded path explanation.",
            "forced_abstention": True
        }
        result["verdict"] = "ABSTAIN_UNGROUNDED"
        return result

    # Critic Pass
    result["critic_audit"] = {
        "passed": True,
        "reason": "All outputs verified grounded with no un-flagged conflicts.",
        "forced_abstention": False
    }
    return result
