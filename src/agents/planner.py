"""
Framelink Agent — Dynamic LangGraph Planner & Tool Router
Analyzes multi-part query intent and dynamically routes execution across the 10 specialist tools in sequence.
"""

import asyncio
import re
from typing import Dict, Any, List

from src.graph.client import hydradb_client
from src.agents.tools.similar_claim_finder import tool_similar_claim_finder
from src.agents.tools.narrative_context_expander import tool_narrative_context_expander
from src.agents.tools.related_claims_via_frame_entity import tool_related_claims_via_frame_entity
from src.agents.tools.evidence_collector import tool_evidence_collector
from src.agents.tools.conflict_detector import tool_conflict_detector
from src.agents.tools.temporal_evolution_analyzer import tool_temporal_evolution_analyzer
from src.agents.tools.entity_bridge_explorer import tool_entity_bridge_explorer
from src.agents.tools.frame_explorer import tool_frame_explorer
from src.agents.tools.statistics_opencypher_fallback import tool_statistics_opencypher_fallback
from src.agents.tools.path_explainer import tool_path_explainer
from src.agents.critic import review_planner_output
from src.agents.memory import save_session_memory

class LangGraphPlannerState:
    def __init__(self, query_text: str, session_id: str = "SESS-001"):
        self.session_id = session_id
        self.query_text = query_text
        self.tools_triggered = []
        self.tool_outputs = {}
        self.verdict = "PENDING"
        self.explanation = ""

def retrieve_exploratory_claims(query_text: str) -> List[Dict[str, Any]]:
    query_lower = query_text.lower()
    
    # 1. Search for target Publisher in graph
    pub_node = None
    for p in hydradb_client.nodes.values():
        if p.get("label") == "Publisher":
            p_name = p.get("name", "").lower()
            if p_name in query_lower or p_name.replace(".org", "") in query_lower:
                pub_node = p
                break
                
    # 2. Search for target Entity in graph
    ent_node = None
    for e in hydradb_client.nodes.values():
        if e.get("label") == "Entity":
            e_name = e.get("name", "").lower()
            if e_name in query_lower or ("cdc" in query_lower and "centers for disease control" in e_name) or ("fda" in query_lower and "food and drug administration" in e_name) or ("who" in query_lower and "world health organization" in e_name) or ("pfizer" in query_lower and "pfizer" in e_name):
                ent_node = e
                break

    matching_claims = []
    
    # Traverse Publisher <- PUBLISHED_BY - FactCheck - CHECKS -> Claim
    if pub_node:
        fc_ids = set()
        for eid, e in hydradb_client.edges.items():
            if e.get("type") == "PUBLISHED_BY" and e.get("target") == pub_node["id"]:
                fc_ids.add(e.get("source"))
        for eid, e in hydradb_client.edges.items():
            if e.get("type") == "CHECKS" and e.get("source") in fc_ids:
                claim_node = hydradb_client.nodes.get(e.get("target"))
                if claim_node and claim_node.get("label") == "Claim":
                    matching_claims.append(claim_node)
                    
        # Apply structural frame filtering if cardiology keywords are present in query
        is_cardio = any(k in query_lower for k in ["heart", "cardiac", "myocarditis", "pericarditis", "clot"])
        if is_cardio:
            frame_node = None
            for n in hydradb_client.nodes.values():
                if n.get("label") == "NarrativeFrame":
                    f_name = n.get("frame_name", "").lower()
                    if any(k in f_name for k in ["cardiovascular", "myocarditis", "heart"]):
                        frame_node = n
                        break
            if frame_node:
                cardio_claims = set()
                for eid, e in hydradb_client.edges.items():
                    if e.get("type") == "USES_FRAME" and e.get("target") == frame_node["id"]:
                        cardio_claims.add(e.get("source"))
                matching_claims = [c for c in matching_claims if c["id"] in cardio_claims]
            
    # Traverse Claim - MENTIONS -> Entity
    elif ent_node:
        for eid, e in hydradb_client.edges.items():
            if e.get("type") == "MENTIONS" and e.get("target") == ent_node["id"]:
                claim_node = hydradb_client.nodes.get(e.get("source"))
                if claim_node and claim_node.get("label") == "Claim":
                    matching_claims.append(claim_node)

    return matching_claims

async def execute_dynamic_planner(query_text: str, session_id: str = "SESS-001") -> Dict[str, Any]:
    """
    Dynamic Tool Router: Analyzes query intent and routes execution through required specialist tools
    """
    state = LangGraphPlannerState(query_text, session_id)
    query_lower = query_text.lower()

    # Detect exploratory multi-result list requests
    is_exploratory = any(k in query_lower for k in ["what else", "what has", "what other", "debunked by", "list of", "claims about", "investigations", "mention"])
    if is_exploratory:
        expl_claims = retrieve_exploratory_claims(query_text)
        if expl_claims:
            explanation = f"I found **{len(expl_claims)} investigations** matching your query:\n\n"
            for idx, c in enumerate(expl_claims):
                explanation += f"{idx+1}. **{c.get('content')}** (Verdict: {c.get('status')})\n"
                explanation += f"   - *Fact-Checker Finding*: {c.get('rating_explanation') or 'No additional details.'}\n"
                if c.get("url"):
                    explanation += f"   - *URL*: [Fact-check investigation report ↗]({c.get('url')})\n"
                explanation += "\n"
                
            tech_trace = (
                "**Exploratory Graph Traversal**\n"
                "- **Path**: Publisher/Entity Node -> Checks/Mentions -> Claim\n"
                f"- **Total Nodes Found**: {len(expl_claims)}"
            )
                
            raw_planner_result = {
                "session_id": session_id,
                "query": query_text,
                "candidate_id": None,
                "tools_triggered": ["RelatedClaimsViaFrameEntity"],
                "tool_outputs": {"RelatedClaimsViaFrameEntity": expl_claims},
                "conflicts_found": [],
                "fact_check_url": expl_claims[0].get("url", ""),
                "source_url": expl_claims[0].get("url", ""),
                "verdict": "EXPLORATION",
                "raw_verdict": "EXPLORATION",
                "explanation": explanation,
                "technical_details": tech_trace
            }
            critic_reviewed = review_planner_output(raw_planner_result)
            save_session_memory(session_id, query_text, critic_reviewed)
            return critic_reviewed

    # Intent Analysis & Dynamic Tool Routing Logic
    is_temporal = any(k in query_lower for k in ["evolv", "history", "timeline", "supersed", "baseline"])
    is_conflict = any(k in query_lower for k in ["conflict", "contradict", "discrepancy", "refute", "incompat"])
    is_similar = any(k in query_lower for k in ["similar", "variant", "resemble", "like"])
    is_bridge = any(k in query_lower for k in ["bridge", "link between", "connect"])

    # 1. Route to Temporal Evolution Analyzer if query asks about narrative evolution
    if is_temporal or "narrative" in query_lower:
        state.tools_triggered.append("TemporalEvolutionAnalyzer")
        state.tool_outputs["TemporalEvolutionAnalyzer"] = await tool_temporal_evolution_analyzer()

    # 2. Route to Similar Claim Finder if similarity requested
    if is_similar:
        state.tools_triggered.append("SimilarClaimFinder")
        state.tool_outputs["SimilarClaimFinder"] = await tool_similar_claim_finder(query_text)

    # 3. Route to Conflict Detector scoped to the queried claims
    state.tools_triggered.append("ConflictDetector")
    state.tool_outputs["ConflictDetector"] = await tool_conflict_detector(query_text=query_text)

    # 4. Route to Path Explainer (Always on for grounded proof provenance)
    state.tools_triggered.append("PathExplainer")
    state.tool_outputs["PathExplainer"] = await tool_path_explainer(query_text=query_text)

    # Combine tool outputs into raw planner result
    conflicts_found = state.tool_outputs.get("ConflictDetector", {}).get("conflicts", [])
    has_conflicts = len(conflicts_found) > 0
    explainer_res = state.tool_outputs.get("PathExplainer", {})
    candidate_id = explainer_res.get("claim_id")
    raw_verdict = explainer_res.get("verdict", "")
    is_grounded = explainer_res.get("is_grounded", True)

    # Grounded verdict determination (mapping to four defined system outcomes)
    if not is_grounded:
        final_verdict = "ABSTAIN_UNGROUNDED"
    elif has_conflicts:
        final_verdict = "ABSTAIN_CONTRADICTORY_EVIDENCE"
    elif raw_verdict:
        v_upper = raw_verdict.upper()
        # 1. FALSE-BASELESS (Red)
        if any(k in v_upper for k in ["FALSE", "BASELESS", "PANTS ON FIRE", "INCORRECT", "FAKE", "UNSUPPORTED", "UNTRUE", "DEBUNKED", "INACCURATE", "WRONG"]):
            final_verdict = "FALSE-BASELESS"
        # 2. MISLEADING (Amber)
        elif any(k in v_upper for k in ["FLAWED", "FLAW", "MISLEADING", "DISTORTS", "EXAGGERAT", "CONTEXT", "HALF", "UNPROVEN", "MIXTURE", "MOSTLY FALSE", "PARTLY"]):
            final_verdict = "MISLEADING"
        # 3. CORROBORATED (Green)
        elif any(k in v_upper for k in ["TRUE", "CORRECT", "ACCURATE", "SUPPORTED", "CORROBORATED", "MOSTLY TRUE"]):
            final_verdict = "CORROBORATED"
        else:
            final_verdict = "MISLEADING"  # Conservative fallback
    else:
        final_verdict = "CORROBORATED"

    raw_planner_result = {
        "session_id": session_id,
        "query": query_text,
        "candidate_id": candidate_id,
        "tools_triggered": state.tools_triggered,
        "tool_outputs": state.tool_outputs,
        "conflicts_found": conflicts_found,
        "fact_check_url": explainer_res.get("fact_check_url", ""),
        "source_url": explainer_res.get("source_url", ""),
        "verdict": final_verdict,
        "raw_verdict": raw_verdict,
        "explanation": explainer_res.get("explanation", ""),
        "technical_details": explainer_res.get("technical_details", "")
    }

    # Step Critic Audit Pass
    critic_reviewed = review_planner_output(raw_planner_result)

    # Step Memory Persistence
    save_session_memory(session_id, query_text, critic_reviewed)

    return critic_reviewed
