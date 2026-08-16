"""
Framelink API — SSE Streaming Endpoint Router
Streams planner tool execution steps and explanations in real-time (/api/v1/stream)
"""

import json
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from src.agents.planner import execute_dynamic_planner

router = APIRouter(prefix="/api/v1", tags=["SSE Streaming API"])

@router.get("/stream")
async def stream_investigation(query: str = "Acme Net Zero 2025"):
    """
    Server-Sent Events (SSE) streaming endpoint emitting tool calls and final explanations
    """
    async def event_generator():
        yield {
            "event": "started",
            "data": json.dumps({"status": "INVESTIGATION_STARTED", "query": query})
        }
        await asyncio.sleep(0.1)

        # Stream tool calls
        res = await execute_dynamic_planner(query, session_id="SESS-STREAM-01")
        for tool_name in res.get("tools_triggered", []):
            yield {
                "event": "tool_call",
                "data": json.dumps({"tool": tool_name, "status": "COMPLETED"})
            }
            await asyncio.sleep(0.05)

        yield {
            "event": "explanation",
            "data": json.dumps({
                "verdict": res.get("verdict"),
                "explanation": res.get("explanation"),
                "critic_audit": res.get("critic_audit")
            })
        }

    return EventSourceResponse(event_generator())
