"""
Framelink API — Ariadne GraphQL Schema & Resolvers
Schema mirroring the graph model for flexible querying beyond REST
"""

from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from src.graph.client import hydradb_client
from src.agents.planner import execute_dynamic_planner

type_defs = """
    type Query {
        claims: [Claim!]!
        claim(id: String!): Claim
        entities: [Entity!]!
        conflicts: [Conflict!]!
        investigate(query: String!): InvestigationResult!
    }

    type Claim {
        id: String!
        label: String!
        title: String
        content: String
        status: String
        entity: String
        category: String
    }

    type Entity {
        id: String!
        label: String!
        name: String
        ticker: String
    }

    type Conflict {
        id: String!
        title: String
        severity: String
        discrepancy: String
    }

    type InvestigationResult {
        verdict: String!
        explanation: String!
        tools_triggered: [String!]!
    }
"""

query = QueryType()

@query.field("claims")
def resolve_claims(*_):
    return [n for n in hydradb_client.nodes.values() if n.get("label") == "Claim"]

@query.field("claim")
def resolve_claim(*_, id: str):
    return hydradb_client.nodes.get(id)

@query.field("entities")
def resolve_entities(*_):
    return [n for n in hydradb_client.nodes.values() if n.get("label") == "Entity"]

@query.field("conflicts")
def resolve_conflicts(*_):
    return [n for n in hydradb_client.nodes.values() if n.get("label") == "Conflict"]

@query.field("investigate")
async def resolve_investigate(*_, query: str):
    res = await execute_dynamic_planner(query, session_id="SESS-GQL-01")
    return {
        "verdict": res.get("verdict", "UNKNOWN"),
        "explanation": res.get("explanation", ""),
        "tools_triggered": res.get("tools_triggered", [])
    }

graphql_schema = make_executable_schema(type_defs, query)
graphql_app = GraphQL(graphql_schema, debug=True)
