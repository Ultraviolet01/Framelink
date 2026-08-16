"""
Framelink Agent Tool — Grounded Path Explainer
Takes a ranked claim and produces a natural-language explanation grounded in actual graph nodes and edges.
Hyperlinks every citation to the real FactCheck report URL or Source appearance URL from the graph data.
Uses claude-haiku-4-5-20251001 with prompt caching for live real-time query explanations.
"""

import os
import json
from typing import Dict, Any, List, Optional
from src.graph.client import hydradb_client
from src.retrieval.candidate_gen import find_candidate_claims
from src.ingest.embed_cluster import compute_embedding

MODEL = "claude-haiku-4-5-20251001"

EXPLAINER_SYSTEM_PROMPT = """You are a fact-checking explanation agent for Framelink.
Explain the verdict and findings in a natural, conversational plain-English paragraph. State the claim, the verdict, and the reason why in normal sentences. Do not use labeled fields, bullet points, or numbered lists.
Only state facts that are directly present in the provided claim text, fact-checker finding, and verdict — do not add, infer, soften, or generalize beyond what's given. Every factual sentence must be traceable to the retrieved data passed to you.
Do not mention internal graph concepts, database details, node IDs (e.g. CLM-xxxx, ENT-xxxx), edge names, or system traces.
Cite the authoritative fact-check with a markdown link: [Publisher Name](URL)."""

def clean_text(s: str) -> str:
    if not s:
        return ""
    return s.replace("\ufffd", '"').replace("\u0093", '"').replace("\u0094", '"').replace("\u0091", "'").replace("\u0092", "'").replace('""', '"').strip()

async def tool_path_explainer(claim_id: Optional[str] = None, query_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Traverses the grounded 1-3 hop neighborhood of the target claim and formats citations with real web URLs.
    """
    # 1. Resolve target claim
    target_node = None
    if claim_id and claim_id in hydradb_client.nodes:
        target_node = hydradb_client.nodes[claim_id]
    elif query_text:
        qvec = compute_embedding(query_text)
        claims = [n for n in hydradb_client.nodes.values() if n.get("label") == "Claim"]
        cands = find_candidate_claims(qvec, claims, top_k=1, query_text=query_text)
        if cands and cands[0].get("similarity_score", 0) >= 0.55:
            claim_id = cands[0]["id"]
            target_node = cands[0]["node"]
        else:
            return {
                "status": "error",
                "explanation": "No relevant evidence found in the graph substrate for this query.",
                "is_grounded": False
            }

    if not target_node:
        return {
            "status": "error",
            "explanation": "No relevant evidence found in the graph substrate for this query.",
            "is_grounded": False
        }

    cid = target_node["id"]
    claim_text = clean_text(target_node.get("content") or target_node.get("title", ""))
    claim_verdict = target_node.get("status", "Unverified")
    claim_cat = target_node.get("category", "General")
    rating_exp = clean_text(target_node.get("rating_explanation", ""))

    # 2. Find connected nodes in 1-2 hop neighborhood
    connected_edges = [e for e in hydradb_client.edges.values() if e["source"] == cid or e["target"] == cid]
    
    fact_check_node = None
    publisher_node = None
    narrative_frame_node = None
    source_node = None
    entity_node = None
    evolved_edges = []
    weakens_edges = []
    contradicts_edges = []

    for e in connected_edges:
        other_id = e["target"] if e["source"] == cid else e["source"]
        other = hydradb_client.nodes.get(other_id, {})
        lbl = other.get("label")
        
        if lbl == "FactCheck":
            if not fact_check_node or (target_node.get("url") and other.get("url") == target_node.get("url")):
                fact_check_node = other
        elif lbl == "Publisher":
            if not publisher_node or (target_node.get("publisher") and other.get("name") == target_node.get("publisher")):
                publisher_node = other
        elif lbl == "NarrativeFrame":
            narrative_frame_node = other
        elif lbl == "Source":
            source_node = other
        elif lbl == "Entity":
            entity_node = other

        if e.get("type") == "EVOLVED_FROM":
            is_source = (e["source"] == cid)
            evolved_edges.append((other, e, is_source))
        elif e.get("type") == "WEAKENS":
            weakens_edges.append((other, e))
        elif e.get("type") == "CONTRADICTS":
            contradicts_edges.append((other, e))

    # Build real citation links
    fc_url = target_node.get("url", "") or (fact_check_node.get("url") if fact_check_node else "")
    fc_pub = target_node.get("publisher", "") or (publisher_node.get("name") if publisher_node else "Fact-Checking Publisher")
    fc_verdict = (fact_check_node.get("verdict") if fact_check_node else "") or claim_verdict
    src_url = (source_node.get("url") if source_node else "") or target_node.get("appearance_url", "")
    src_title = (source_node.get("title") if source_node else "") or "Primary Claim Appearance"

    # Format structured reasoning chain with genuine web URLs
    steps = [
        f"1. **Investigated Claim** (`{cid}`): \"{claim_text}\"",
        f"   - **Canonical Verdict**: `{fc_verdict}`",
        f"   - **Topical Category**: {claim_cat}"
    ]

    step_counter = 2

    if fc_url:
        steps.append(f"{step_counter}. **Authoritative Fact-Check**: [{fc_pub} Investigation Report]({fc_url})")
        step_counter += 1
    else:
        steps.append(f"{step_counter}. **Authoritative Fact-Check**: {fc_pub} (Verdict: `{fc_verdict}`)")
        step_counter += 1

    if rating_exp:
        steps.append(f"   - **Fact-Checker Finding**: \"{rating_exp}\"")

    if src_url:
        steps.append(f"{step_counter}. **Original Claim Origin**: [{src_title}]({src_url})")
        step_counter += 1
    elif source_node:
        steps.append(f"{step_counter}. **Original Claim Origin**: {src_title}")
        step_counter += 1

    if narrative_frame_node:
        steps.append(f"{step_counter}. **Knowledge Graph Narrative Frame**: `{narrative_frame_node.get('frame_name')}`")
        step_counter += 1

    if entity_node:
        steps.append(f"{step_counter}. **Linked Entity**: `{entity_node.get('name')}`")
        step_counter += 1

    if evolved_edges:
        ev_node, ev_edge, is_source = evolved_edges[0]
        reason = clean_text(ev_edge.get("evolution_reasoning", ""))
        ev_text = clean_text(ev_node.get("content", ev_node.get("title", "")))
        if is_source:
            steps.append(f"{step_counter}. **Temporal Evolution Lineage** (`EVOLVED_FROM`): Mutated from earlier claim `{ev_node.get('id')}` (\"{ev_text[:50]}...\") - *{reason}*")
        else:
            steps.append(f"{step_counter}. **Temporal Evolution Lineage** (`EVOLVED_FROM`): Evolved into later claim `{ev_node.get('id')}` (\"{ev_text[:50]}...\") - *{reason}*")
        step_counter += 1

    if weakens_edges:
        w_node, _ = weakens_edges[0]
        w_text = clean_text(w_node.get('content', ''))
        steps.append(f"{step_counter}. **Evidence Tension** (`WEAKENS`): Connected to undermining evidence `{w_node.get('id')}` (\"{w_text[:50]}...\")")
        step_counter += 1

    if contradicts_edges:
        c_node, _ = contradicts_edges[0]
        lbl_c = c_node.get("label")
        if lbl_c == "Conflict":
            c_text = clean_text(c_node.get("discrepancy") or c_node.get("title", ""))
            steps.append(f"{step_counter}. **Active Contradiction** (`CONTRADICTS`): Mutually exclusive with claim conflict `{c_node.get('id')}` - *{c_text}*")
        else:
            c_text = clean_text(c_node.get('content', ''))
            steps.append(f"{step_counter}. **Active Contradiction** (`CONTRADICTS`): Mutually exclusive with claim `{c_node.get('id')}` (\"{c_text[:50]}...\")")
        step_counter += 1

    reasoning_chain = "\n".join(steps)
    
    # Fallback explanation if API is offline
    fallback_link = f" [{fc_pub} investigation report ↗]({fc_url})" if fc_url else f" ({fc_pub})"
    explanation_text = f"The claim \"{claim_text}\" was investigated by {fc_pub} and found to be `{fc_verdict}`.{fallback_link}"
    if rating_exp:
        explanation_text += f" The fact-checkers concluded that: \"{rating_exp}\""

    # Live synthesis with Claude Haiku using prompt caching
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            llm_payload = {
                "claim_id": cid,
                "claim_text": claim_text,
                "verdict": fc_verdict,
                "publisher": fc_pub,
                "fact_check_url": fc_url,
                "source_appearance_url": src_url,
                "rating_explanation": rating_exp,
                "narrative_frame": narrative_frame_node.get("frame_name") if narrative_frame_node else None,
                "evolution_reasoning": evolved_edges[0][1].get("evolution_reasoning") if evolved_edges else None
            }
            resp = client.messages.create(
                model=MODEL,
                max_tokens=350,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": EXPLAINER_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": f"Graph Evidence: {json.dumps(llm_payload)}"}]
            )
            # Use the plain-English response directly
            explanation_text = resp.content[0].text
        except Exception:
            pass

    return {
        "claim_id": cid,
        "verdict": fc_verdict,
        "explanation": explanation_text,
        "technical_details": reasoning_chain,
        "fact_check_url": fc_url,
        "source_url": src_url,
        "is_grounded": True
    }
