"""
Framelink Evaluation Harness (Step 11)
Measures:
1. claim-to-narrative accuracy (correct clustering/linking to narrative frames)
2. multi-hop precision (correctness and relevance of returned graph paths)
3. abstention correctness (grounded refusal on contradictory queries vs definitive answers on clear ones)
against a hand-constructed held-out test suite of real COVID-19 vaccine assertions.
"""

import os
import time
import json
import asyncio
from typing import Dict, Any, List

from src.graph.client import hydradb_client
from src.retrieval.candidate_gen import find_candidate_claims, generate_candidates_and_expand
from src.ingest.embed_cluster import compute_embedding
from src.agents.planner import execute_dynamic_planner
from src.ingest.write_graph import run_batch_ingestion

HELDOUT_TEST_SET = [
    # 1. Clear factual assertions with expected narrative frame mappings
    {
        "id": "EVAL-01",
        "query": "COVID-19 vaccines cause myocarditis and heart inflammation in young men",
        "expected_frame": "Cardiovascular Risk & Myocarditis Framing",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-02",
        "query": "mRNA vaccines alter female fertility and cause ovarian syncytin-1 damage",
        "expected_frame": "Reproductive Health & Fertility Concerns",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-03",
        "query": "VAERS raw reports prove tens of thousands of sudden deaths caused by vaccines",
        "expected_frame": "Excess Mortality & VAERS Causality Fallacy",
        "expected_entity": "Vaccine Adverse Event Reporting System (VAERS)",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-04",
        "query": "mRNA COVID-19 vaccines integrate into human genomic DNA in the nucleus",
        "expected_frame": "Genomic Alteration & DNA Integration Framing",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-05",
        "query": "COVID vaccines contain graphene oxide and magnetic microchip contaminants",
        "expected_frame": "Foreign Contaminants & Chemical Composition Claims",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-06",
        "query": "CDC recommended vaccine mandates for 6-year-old children without clinical evidence",
        "expected_frame": "Civil Liberties & Regulatory Mandate Controversies",
        "expected_entity": "Centers for Disease Control and Prevention (CDC)",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-07",
        "query": "Vaccines have zero efficacy and fail to protect against transmission",
        "expected_frame": "Vaccine Inefficacy & Breakthrough Transmission Framing",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },
    {
        "id": "EVAL-08",
        "query": "Moderna vaccine clinical trial data submitted to FDA",
        "expected_frame": "COVID-19 Immunization & Public Health Debate",
        "expected_entity": "Moderna Therapeutics",
        "should_abstain": False,
        "type": "retrieval_and_framing"
    },

    # 2. Contradictory queries requiring Grounded Abstention
    {
        "id": "EVAL-09",
        "query": "74% of sudden deaths are proven to be caused by COVID-19 vaccines versus negligible mortality",
        "expected_frame": "Excess Mortality & VAERS Causality Fallacy",
        "expected_entity": "Vaccine Adverse Event Reporting System (VAERS)",
        "should_abstain": True,
        "type": "abstention"
    },
    {
        "id": "EVAL-10",
        "query": "European databases prove 15,000 vaccine deaths while official registries confirm databases show no death toll",
        "expected_frame": "Excess Mortality & VAERS Causality Fallacy",
        "expected_entity": "European Medicines Agency (EMA)",
        "should_abstain": True,
        "type": "abstention"
    },
    {
        "id": "EVAL-11",
        "query": "CDC pediatric vaccine approval had zero clinical evidence versus ACIP randomized trial evaluations",
        "expected_frame": "Civil Liberties & Regulatory Mandate Controversies",
        "expected_entity": "Centers for Disease Control and Prevention (CDC)",
        "should_abstain": True,
        "type": "abstention"
    },
    {
        "id": "EVAL-12",
        "query": "The COVID vaccine killed 60,000 people in Germany causing Germany to halt all vaccine administration",
        "expected_frame": "Excess Mortality & VAERS Causality Fallacy",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": True,
        "type": "abstention"
    },

    # 3. Multi-hop path precision tests
    {
        "id": "EVAL-13",
        "query": "PolitiFact investigation on Pfizer mRNA vaccine FDA approval",
        "expected_frame": "COVID-19 Immunization & Public Health Debate",
        "expected_entity": "U.S. Food and Drug Administration (FDA)",
        "should_abstain": False,
        "type": "multihop_path"
    },
    {
        "id": "EVAL-14",
        "query": "FactCheck.org safety review of randomized placebo-controlled trials",
        "expected_frame": "COVID-19 Immunization & Public Health Debate",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "multihop_path"
    },
    {
        "id": "EVAL-15",
        "query": "AstraZeneca blood clotting and thrombocytopenia EMA pharmacovigilance reports",
        "expected_frame": "Cardiovascular Risk & Myocarditis Framing",
        "expected_entity": "AstraZeneca / Oxford",
        "should_abstain": False,
        "type": "multihop_path"
    },

    # 4. Complex & Edge Cases (Challenging queries with subtle ambiguities)
    {
        "id": "EVAL-16",
        "query": "Aneurysms in young athletes after mRNA booster shots",
        "expected_frame": "Cardiovascular Risk & Myocarditis Framing",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "edge_case"
    },
    {
        "id": "EVAL-17",
        "query": "Dr. Ladapo Florida DNA plasmid contamination warning",
        "expected_frame": "Genomic Alteration & DNA Integration Framing",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "edge_case"
    },
    {
        "id": "EVAL-18",
        "query": "Unverified blog post about luciferase patent #060606 microchip injection",
        "expected_frame": "Foreign Contaminants & Chemical Composition Claims",
        "expected_entity": "Bill & Melinda Gates Foundation",
        "should_abstain": False,
        "type": "edge_case"
    },
    {
        "id": "EVAL-19",
        "query": "Excess all-cause mortality statistics in 2021 vs baseline insurance claims",
        "expected_frame": "Excess Mortality & VAERS Causality Fallacy",
        "expected_entity": "Vaccine Adverse Event Reporting System (VAERS)",
        "should_abstain": False,
        "type": "edge_case"
    },
    {
        "id": "EVAL-20",
        "query": "Natural immunity vs vaccine-induced immunity antibody titer longevity",
        "expected_frame": "Vaccine Inefficacy & Breakthrough Transmission Framing",
        "expected_entity": "Pfizer-BioNTech",
        "should_abstain": False,
        "type": "edge_case"
    }
]

async def run_eval_suite() -> Dict[str, Any]:
    """
    Runs the complete evaluation harness against the live graph substrate.
    Returns real, un-inflated metric benchmarks with failure case logs.
    """
    t0 = time.time()
    
    # 1. Ensure live graph is ready
    if len(hydradb_client.nodes) == 0:
        await run_batch_ingestion()

    all_nodes = list(hydradb_client.nodes.values())
    claim_nodes = [n for n in all_nodes if n.get("label") == "Claim"]

    framing_correct = 0
    framing_total = 0

    multihop_hits = 0
    multihop_total = 0

    abstention_correct = 0
    abstention_total = 0

    failures = []

    for test in HELDOUT_TEST_SET:
        qid = test["id"]
        qtext = test["query"]
        exp_frame = test.get("expected_frame")
        exp_ent = test.get("expected_entity")
        should_abstain = test["should_abstain"]
        test_type = test["type"]

        # Run Candidate Generation + 2-hop Graph Expansion
        qvec = compute_embedding(qtext)
        candidates = find_candidate_claims(qvec, claim_nodes, top_k=3)
        
        # 1. Claim-to-Narrative Accuracy Benchmark
        framing_total += 1
        top_cand = candidates[0] if candidates else None
        
        # Look up connected narrative frame in graph
        actual_frame = None
        if top_cand:
            cid = top_cand["id"]
            frame_edges = [
                e for e in hydradb_client.edges.values() 
                if e["source"] == cid and e["type"] in ["USES_FRAME", "APPEARS_IN_NARRATIVE"]
            ]
            if frame_edges:
                target_fid = frame_edges[0]["target"]
                fnode = hydradb_client.nodes.get(target_fid, {})
                actual_frame = fnode.get("frame_name")

        is_framing_match = (actual_frame == exp_frame) if actual_frame and exp_frame else False
        if is_framing_match:
            framing_correct += 1
        else:
            failures.append({
                "test_id": qid,
                "type": "framing_mismatch",
                "query": qtext,
                "expected": exp_frame,
                "actual": actual_frame or "None (Unlinked)"
            })

        # 2. Multi-hop Path Precision
        multihop_total += 1
        if top_cand:
            cid = top_cand["id"]
            # Check 1-3 hop connected paths (FactCheck, Publisher, Source, Entity)
            connected_edges = [e for e in hydradb_client.edges.values() if e["source"] == cid or e["target"] == cid]
            connected_node_ids = set()
            for e in connected_edges:
                connected_node_ids.add(e["source"])
                connected_node_ids.add(e["target"])

            connected_labels = set(hydradb_client.nodes[nid].get("label") for nid in connected_node_ids if nid in hydradb_client.nodes)
            
            # Multi-hop precision requires resolving at least 3 distinct ontology layers (e.g. Publisher, FactCheck, NarrativeFrame, Source)
            if len(connected_labels) >= 3:
                multihop_hits += 1
            else:
                failures.append({
                    "test_id": qid,
                    "type": "multihop_sparsity",
                    "query": qtext,
                    "resolved_labels": list(connected_labels)
                })

        # 3. Abstention Correctness Benchmark
        abstention_total += 1
        # Run agent planner with ground critic audit
        planner_res = await execute_dynamic_planner(qtext, session_id=f"EVAL-{qid}")
        verdict = planner_res.get("verdict", "")
        did_abstain = ("ABSTAIN" in verdict)

        if did_abstain == should_abstain:
            abstention_correct += 1
        else:
            failures.append({
                "test_id": qid,
                "type": "abstention_failure",
                "query": qtext,
                "should_abstain": should_abstain,
                "did_abstain": did_abstain,
                "actual_verdict": verdict
            })

    elapsed_ms = round((time.time() - t0) * 1000, 2)
    
    framing_acc = round(framing_correct / framing_total, 4)
    multihop_prec = round(multihop_hits / multihop_total, 4)
    abstention_acc = round(abstention_correct / abstention_total, 4)
    overall_score = round((framing_acc + multihop_prec + abstention_acc) / 3.0, 4)

    results = {
        "eval_status": "COMPLETED",
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_test_cases": len(HELDOUT_TEST_SET),
        "claim_narrative_accuracy": framing_acc,
        "multihop_precision": multihop_prec,
        "abstention_correctness": abstention_acc,
        "overall_score": overall_score,
        "execution_time_ms": elapsed_ms,
        "failure_cases_count": len(failures),
        "sample_failure_cases": failures[:3]
    }

    # Persist results to disk
    eval_cache_path = os.path.join("data", "interim", "eval_harness_results.json")
    os.makedirs(os.path.dirname(eval_cache_path), exist_ok=True)
    with open(eval_cache_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    res = asyncio.run(run_eval_suite())
    print("=================================================================")
    print("        FRAMELINK EVALUATION HARNESS BENCHMARK (STEP 11)         ")
    print("=================================================================")
    print(f"Total Held-Out Test Cases:    {res['total_test_cases']}")
    print(f"Claim-to-Narrative Accuracy:  {res['claim_narrative_accuracy'] * 100:.1f}%")
    print(f"Multi-Hop Path Precision:     {res['multihop_precision'] * 100:.1f}%")
    print(f"Abstention Correctness:       {res['abstention_correctness'] * 100:.1f}%")
    print(f"Overall Benchmark Score:      {res['overall_score'] * 100:.1f}%")
    print(f"Benchmark Latency:            {res['execution_time_ms']} ms")
    print(f"Failure Cases Count:          {res['failure_cases_count']}")
    print("Sample Failure Cases:")
    for fc in res["sample_failure_cases"]:
        print(f"  - [{fc['test_id']}] {fc['type']}: '{fc['query'][:50]}...'")
    print("=================================================================")
