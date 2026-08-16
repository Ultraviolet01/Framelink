"""
Framelink API — Model Context Protocol (MCP) Server
Exposes Framelink claim investigation tools as FastMCP tools for external AI agents
"""

import asyncio
from typing import Dict, Any

try:
    from mcp.server.fastmcp import FastMCP
    mcp_app = FastMCP("framelink-factchecker")

    @mcp_app.tool()
    async def investigate_claim(query_text: str) -> str:
        """
        Investigates a corporate claim against HydraDB graph substrate using multi-tool orchestration
        """
        from src.agents.planner import execute_dynamic_planner
        res = await execute_dynamic_planner(query_text, session_id="SESS-MCP-01")
        return f"Verdict: {res.get('verdict')}\nExplanation:\n{res.get('explanation')}"

except Exception:
    mcp_app = None

async def run_mcp_tool_execution(query_text: str) -> Dict[str, Any]:
    """Fallback runner for direct MCP tool calls"""
    from src.agents.planner import execute_dynamic_planner
    res = await execute_dynamic_planner(query_text, session_id="SESS-MCP-01")
    return {
        "mcp_tool": "investigate_claim",
        "query": query_text,
        "result": f"Verdict: {res.get('verdict')}\nExplanation:\n{res.get('explanation')}",
        "raw_response": res
    }
