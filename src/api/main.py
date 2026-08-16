"""
Framelink API — Main Application Assembly
Assembles FastAPI REST router, Ariadne GraphQL app (/graphql), SSE streaming router (/api/v1/stream), and static UIs
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import CORSMiddleware
from src.api.rest import router as rest_router
from src.api.streaming import router as streaming_router
from src.api.graphql_schema import graphql_app

app = FastAPI(
    title="Framelink API",
    description="Multi-Protocol Enterprise Graph Fact-Checking Engine backed by HydraDB",
    version="3.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST & Streaming Routers
app.include_router(rest_router)
app.include_router(streaming_router)

# Mount GraphQL App at /graphql
app.mount("/graphql", graphql_app)

from src.graph.client import hydradb_client
from src.ingest.write_graph import run_batch_ingestion

@app.on_event("startup")
async def startup_event():
    if len(hydradb_client.nodes) == 0:
        await run_batch_ingestion()

# Serve Web UIs
chat_ui_primary = "framelink-chat-ui(2).html"
chat_ui_path = os.path.join("web", "chat", "index.html")
admin_ui_path = os.path.join("web", "admin", "index.html")

@app.get("/", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    for p in [chat_ui_primary, chat_ui_path]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>Framelink Investigator Portal</h1>"

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    if os.path.exists(admin_ui_path):
        with open(admin_ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Framelink Admin Dashboard</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
