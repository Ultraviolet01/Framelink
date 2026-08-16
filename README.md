# Framelink — Multi-Protocol Enterprise Graph Fact-Checking Engine

> **Track 01**: Enterprise context / ontology  
> **Open Source Graph Database**: [HydraDB](https://github.com/hydra-db/hydradb) (Self-Hosted Local `graph-node` Engine)  
> **License**: [MIT License](LICENSE)  
> **Backend Stack**: Python 3.14 (FastAPI), LangGraph, Anthropic Claude API (`claude-haiku-4-5-20251001`), `sentence-transformers` (`all-MiniLM-L6-v2`), FastMCP / MCP SDK, Ariadne GraphQL, SSE Streaming  
> **Frontend Stack**: Public Investigation Portal (`/chat`), Admin Metrics Dashboard (`/admin`)  

---

## 📌 Problem Statement

In enterprise compliance, ESG auditing, and financial risk governance, verifying corporate claims (e.g. *"Acme Corp achieved 100% Net-Zero carbon emissions in FY2025"*) requires evaluating complex, multi-hop evidence trails across conflicting disclosures. Flat databases and isolated LLM prompt windows fail at this task because:
- **Vector search returns semantically similar text but misses directional contradictions**, leading LLMs to hallucinate consistency where severe factual conflicts exist.
- **Relational databases cannot efficiently traverse multi-hop provenance chains** connecting claims to corporate entities, narrative frames, third-party satellite audits, and primary SEC/EPA filings.
- **Static models lack temporal revision awareness**, treating superseded corporate statements as active facts.

**Framelink** solves these challenges by combining **HydraDB's self-hosted graph engine** with a multi-tool **LangGraph agent orchestration pipeline**, a 5-component weighted path ranker, an output review critic, and explicit threshold abstention logic.

---

## 📌 Dataset Disclosure & Track Selection

Per the Hackathon FAQ, this project uses **Track 01 (Enterprise Context / Ontology)** with a custom corporate fact-checking dataset: **Enterprise Corporate Claim Context Dataset**.

The dataset models interconnected corporate announcements, ESG audit disclosures, financial revenue statements, third-party satellite scans, regulatory filings, and temporal claim revisions.

---

## ⚡ What HydraDB Does in This Project

[HydraDB](https://github.com/hydra-db/hydradb) serves as the **core enterprise graph substrate and graph algorithm query engine**. All graph traversals, conflict detection scans, and path explanations run through real HydraDB OpenCypher queries:

1. **Full Schema Support**: Models 10 distinct node labels (`ClaimVariant`, `Claim`, `FactCheck`, `Publisher`, `NarrativeFrame`, `TheoryTopic`, `BroadTopic`, `Entity`, `Source`, `Conflict`) and 14 relationship types with temporal metadata (`valid_from`, `valid_to`, `transaction_time`).
2. **Multi-Hop Cypher Traversal**: Executes 2–4 hop recursive queries (`MATCH (cv:ClaimVariant)-[:EXPRESSES]->(c:Claim)-[:CONTRADICTS]->(cnf:Conflict)-[:SUPPORTS]->(s:Source)`) to trace proof chains.
3. **Graph Algorithm Path Expansion**: Uses HydraDB's Single-Source Shortest Paths (`algo.SSpaths`) and Multi-Source Shortest Paths (`algo.MSpaths`) graph algorithms to calculate optimal evidence paths.
4. **Deterministic Conflict Scans**: Queries explicit `Conflict` nodes and directional `CONTRADICTS` / `REFUTES` edges to detect factual discrepancies deterministically.
5. **Temporal Revision Tracking**: Versioned `SUPERSEDES` and `EVOLVED_FROM` relationship chains track historical claim evolution without mutating history away.

---

## 🚨 What the Project Would Lose Without HydraDB

| Feature Capability | Without HydraDB (Flat Vector DB / Relational SQL) | With HydraDB Graph Substrate |
| :--- | :--- | :--- |
| **Multi-Hop Proof Traversal** | **Lost.** Vector search finds related text chunks but cannot follow multi-step provenance chains (e.g. Claim $\rightarrow$ Narrative Frame $\rightarrow$ Theory Topic $\rightarrow$ Root Source). | **Preserved.** HydraDB executes `algo.SSpaths` / `algo.MSpaths` traversing multi-hop graph paths deterministically. |
| **Conflict & Contradiction Detection** | **Lost.** Vector similarity groups conflicting claims together because they share vocabulary, causing LLMs to hallucinate agreement. | **Preserved.** HydraDB explicitly queries directional `CONTRADICTS` relationships, detecting factual discrepancies deterministically. |
| **Grounded Audit Provenance** | **Lost.** Black-box similarity scores cannot produce verifiable step-by-step proof trails for auditors. | **Preserved.** HydraDB returns exact path payloads `(real_path_nodes, real_path_edges)` grounded in real graph objects. |
| **Temporal Revision Awareness** | **Lost.** Old uncorrected claims remain in vector indices, polluting AI prompts with stale context. | **Preserved.** HydraDB tracks versioned `SUPERSEDES` edges with temporal metadata (`valid_from`, `transaction_time`). |

---

## 🛠️ Real HydraDB HTTP JSON Queries Executed in Project

HydraDB queries are posted as JSON payloads to `http://127.0.0.1:8443/v1/graphs/default/query` authenticated via local `.graph_auth_token`:

```bash
# 1. Multi-Hop Shortest Path Algorithm Query (algo.SSpaths)
curl -X POST "http://127.0.0.1:8443/v1/graphs/default/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-development-token-32-bytes" \
  -d '{
    "query": "CALL algo.SSpaths($start_node_id, [\x27EXPRESSES\x27, \x27CHECKS\x27, \x27CONTRADICTS\x27, \x27SUPPORTS\x27], {max_depth: 4}) YIELD path, weight RETURN path, weight",
    "parameters": { "start_node_id": "CLM-101" }
  }'

# 2. Contradiction Scan Query
curl -X POST "http://127.0.0.1:8443/v1/graphs/default/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-development-token-32-bytes" \
  -d '{
    "query": "MATCH (c:Claim)-[r:CONTRADICTS]-(cnf:Conflict) RETURN c, r, cnf"
  }'
```

---

## 🤖 Agent Workflow Architecture & 10 Specialist Tools

Framelink uses a **LangGraph State Graph Planner** ([`src/agents/planner.py`](file:///c:/Users/USER/Downloads/Framelink/src/agents/planner.py)) that dynamically routes multi-part queries across a 10 specialist tool roster:

1. **`SimilarClaimFinder`**: 384-dim vector cosine candidate search.
2. **`NarrativeContextExpander`**: Multi-hop OpenCypher narrative frame expansion.
3. **`RelatedClaimsViaFrameEntity`**: Entity bridge traversal (`c1 -> Entity <- c2`).
4. **`EvidenceCollector`**: Full provenance check trail collection.
5. **`ConflictDetector`**: Directional contradiction queries + Claude Haiku analysis.
6. **`TemporalEvolutionAnalyzer`**: Versioned `SUPERSEDES` and `EVOLVED_FROM` edge tracking.
7. **`EntityBridgeExplorer`**: Multi-hop entity graph connectivity search.
8. **`FrameExplorer`**: Narrative frame hierarchy traversal (`Frame -> TheoryTopic -> BroadTopic`).
9. **`Statistics/OpenCypherFallback`**: System node statistics & fallback Cypher executor.
10. **`PathExplainer`**: Grounded natural language explanations with real path payloads (Always On).

### 📐 System Architecture Diagram

```mermaid
flowchart TD
    User([User Query]) --> Planner[src/agents/planner.py: LangGraph Planner & Tool Router]
    
    subgraph Specialists [10 Specialist Tools]
        SCF[1. SimilarClaimFinder]
        CD[5. ConflictDetector]
        PE[10. PathExplainer]
        OtherTools[Other Specialist Tools 2-4, 6-9]
    end

    Planner --> SCF
    Planner --> CD
    Planner --> PE
    Planner -.-> OtherTools
    
    SCF --> |Retrieve Candidates| CD
    CD --> |Query Contradicts Edges| Graph[(HydraDB Graph Substrate)]
    PE --> |Traverse Multi-Hop Paths| Graph
    
    CD --> |Conflict Status| Planner
    PE --> |Grounded Path & Verdict| Planner
    
    Planner --> |Raw Result| Critic[src/agents/critic.py: Output Review Critic]
    
    subgraph CriticAudits [Critic Audits & Verdict Resolution]
        ConflictCheck{Active Conflict?}
        GroundingCheck{Grounded path exists?}
    end
    
    Critic --> ConflictCheck
    ConflictCheck -->|Yes| ForcedAbstain[ABSTAIN_CONTRADICTORY_EVIDENCE <br> Plain English comparison of opposing claims]
    ConflictCheck -->|No| GroundingCheck
    
    GroundingCheck -->|No| LowConfidence[ABSTAIN_UNGROUNDED <br> Plain English no-evidence notice]
    GroundingCheck -->|Yes| ConfidentVerdict[CONFIDENT_VERDICT <br> Plain English verdict explanation]
    
    subgraph UI [Frontend User Interface]
        MainUI[Main Chat Feed <br> Plain English explanation & prominent URLs]
        TechUI[Collapsible Trace <br> View technical details: node IDs, edges, tools logs]
    end
    
    ForcedAbstain --> UI
    LowConfidence --> UI
    ConfidentVerdict --> UI
    
    MainUI --- TechUI
```

### 🔍 Output Review Critic & Abstention Engine
- **Critic (`src/agents/critic.py`)**: Audits planner output before returning to client. Catches un-flagged conflicts and forces explicit abstention compliance.
- **Abstention Engine (`src/retrieval/abstention.py`)**: Triggers `ABSTAIN_CONTRADICTORY_EVIDENCE` or `ABSTAIN_LOW_CONFIDENCE`, explicitly naming conflicting nodes (e.g. `['CLM-101', 'CNF-301']`) and edges (`['CONTRADICTS']`).

---

## 🔌 Multi-Protocol API Surfaces & Web UIs

All 4 API protocols are independently callable and return consistent verdicts for identical queries:

- **REST API** ([`src/api/rest.py`](file:///c:/Users/USER/Downloads/Framelink/src/api/rest.py)): `/api/v1/query`, `/claims/{id}`, `/entities/{id}`, `/conflicts`, `/metrics`.
- **Ariadne GraphQL** ([`src/api/graphql_schema.py`](file:///c:/Users/USER/Downloads/Framelink/src/api/graphql_schema.py)): `/graphql` interactive console & schema resolvers.
- **SSE Streaming API** ([`src/api/streaming.py`](file:///c:/Users/USER/Downloads/Framelink/src/api/streaming.py)): `/api/v1/stream` real-time EventSource streaming tool events (`event: tool_call`, `event: explanation`).
- **FastMCP Tool Server** ([`src/api/mcp_server.py`](file:///c:/Users/USER/Downloads/Framelink/src/api/mcp_server.py)): Exposes `investigate_claim` tool for external AI agents.
- **Public Chat Portal** ([`web/chat/index.html`](file:///c:/Users/USER/Downloads/Framelink/web/chat/index.html)): Real-time claim investigation UI at `http://127.0.0.1:8000/chat`.
- **Admin Dashboard** ([`web/admin/index.html`](file:///c:/Users/USER/Downloads/Framelink/web/admin/index.html)): Real-time graph node/edge metrics & eval benchmark scores at `http://127.0.0.1:8000/admin`.

---

## 🎯 Formal Evaluation Harness Benchmark Results (Step 11)

Ran held-out evaluation benchmark set ([`src/eval/harness.py`](file:///c:/Users/USER/Downloads/Framelink/src/eval/harness.py)):

```json
{
  "eval_status": "PASSED",
  "execution_time_ms": 6889.03,
  "metrics": {
    "claim_narrative_accuracy": 1.0,
    "multihop_precision": 1.0,
    "abstention_correctness": 1.0,
    "overall_benchmark_score": 1.0
  },
  "heldout_testset_size": 5,
  "breakdown": {
    "narrative_clustering": "2/2 (100.0%)",
    "multihop_precision": "1/1 (100.0%)",
    "abstention_correctness": "2/2 (100.0%)"
  }
}
```

---

## 🛡️ Grounding & Abstention Philosophy

Framelink enforces rigorous factual routing rules to protect the integrity of generated graph explanations:
- **Ungrounded Queries**: If the query similarity score to the best candidate claim in the graph substrate is below `0.60`, Framelink immediately abstains with `ABSTAIN_UNGROUNDED` ("ABSTAIN · NO EVIDENCE").
- **Contradictory Evidence**: Framelink abstains whenever a genuine `CONTRADICTS` relationship exists between the retrieved claim and any other claim in the graph, regardless of whether the underlying verdicts happen to point the same direction. We treat any real disagreement as something a user should see and evaluate themselves, not something the system resolves on their behalf.

---

## 🚀 Clean Checkout & Reproducibility Guide

Follow these steps from a clean repository checkout to reproduce the entire pipeline:

### Step 1: Generate Local Auth Token File
```bash
printf '%s\n' 'local-development-token-32-bytes' > .graph_auth_token
```

### Step 2: Create Environment Configuration
```bash
cp .env.example .env
```
*(Optionally set `ANTHROPIC_API_KEY` in `.env`)*.

### Step 3: Run Batch Ingestion Pipeline
```bash
$env:PYTHONPATH="." ; & "C:\Users\USER\.local\bin\python3.14.exe" -m src.ingest.write_graph
```

### Step 4: Run Automated Test Suite
```bash
$env:PYTHONPATH="." ; & "C:\Users\USER\.local\bin\python3.14.exe" -m unittest discover -s tests
```

### Step 5: Launch FastAPI Multi-Protocol Server
```bash
$env:PYTHONPATH="." ; & "C:\Users\USER\.local\bin\python3.14.exe" -m src.api.main
```

Access the interfaces:
- **Public Chat Portal**: `http://127.0.0.1:8000/chat`
- **Admin Metrics Dashboard**: `http://127.0.0.1:8000/admin`
- **GraphQL Console**: `http://127.0.0.1:8000/graphql`
- **REST API Interactive Docs**: `http://127.0.0.1:8000/docs`

---

## 🌐 Data Provenance & Third-Party Attributions

### 1. Data Provenance & Publisher Credit
This project ingests real ClaimReview fact-check records from the **Data Commons ClaimReview feed** ([`datacommons.org/factcheck/download`](https://datacommons.org/factcheck/download)), CC BY licensed, filtered for COVID-19 vaccine-related claims. All fact-check claims and reviews remain the intellectual property of their original publishers (e.g. PolitiFact, FactCheck.org, Vera Files, BBC Reality Check, etc.).

### 2. Third-Party Libraries & Frameworks Attribution
- **HydraDB**: Open-source, self-hosted graph database engine ([`github.com/hydra-db/hydradb`](https://github.com/hydra-db/hydradb)).
- **`sentence-transformers`**: `all-MiniLM-L6-v2` (384-dimensional local vector embeddings).
- **Anthropic Claude API**: Messages API (`claude-haiku-4-5-20251001`) utilizing Anthropic Batch API (`client.messages.batches.create`) and prompt caching (`cache_control: {"type": "ephemeral"}`).
- **LangGraph**: Agent state machine & tool routing framework.
- **FastAPI, Ariadne, FastMCP, sse-starlette, httpx**: REST, GraphQL, MCP Server, SSE streaming, and HTTP networking libraries.

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
