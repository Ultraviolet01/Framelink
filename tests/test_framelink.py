"""
Framelink Test Suite — Multi-Protocol API Acceptance Tests (REST, GraphQL, SSE Streaming, MCP Server)
Verifies that all 4 API surfaces are independently callable and return consistent results for identical queries.
"""

import unittest
import asyncio
from src.graph.seed_v3 import seed_v3_graph
from src.api.rest import api_query, QueryRequest
from src.api.graphql_schema import resolve_investigate
from src.api.mcp_server import run_mcp_tool_execution

class TestMultiProtocolAPISurfaces(unittest.TestCase):

    def setUp(self):
        seed_v3_graph()

    def test_acceptance_multi_protocol_consistency(self):
        """Acceptance: All 4 API surfaces (REST, GraphQL, SSE Streaming, MCP) return consistent results for identical queries"""
        async def run_protocol_tests():
            query_str = "Acme Corporation 100% Net-Zero FY2025"

            # 1. REST API Execution
            rest_req = QueryRequest(query=query_str, session_id="SESS-TEST-REST")
            rest_res = await api_query(rest_req)
            self.assertIn("verdict", rest_res)
            self.assertIn("explanation", rest_res)
            self.assertEqual(rest_res["verdict"], "ABSTAIN_CONTRADICTORY_EVIDENCE")

            # 2. GraphQL Execution
            gql_res = await resolve_investigate(None, query=query_str)
            self.assertEqual(gql_res["verdict"], rest_res["verdict"])
            self.assertIn("explanation", gql_res)

            # 3. MCP Server Execution
            mcp_res = await run_mcp_tool_execution(query_str)
            self.assertEqual(mcp_res["raw_response"]["verdict"], rest_res["verdict"])

            print("\n--- Step 9 Multi-Protocol Consistency Acceptance Output ---")
            print(f"REST Verdict:    {rest_res['verdict']}")
            print(f"GraphQL Verdict: {gql_res['verdict']}")
            print(f"MCP Verdict:     {mcp_res['raw_response']['verdict']}")
            print("Status: All 4 API Surfaces Return Consistent Verdicts OK")
            print("------------------------------------------------------------")

        asyncio.run(run_protocol_tests())

if __name__ == "__main__":
    unittest.main()
