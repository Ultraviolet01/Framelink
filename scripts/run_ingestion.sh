#!/usr/bin/env bash
# Framelink Batch Ingestion Script
echo "============================================================"
echo "Starting Framelink Batch Ingestion Pipeline into HydraDB..."
echo "Google Fact Check Tools API -> Normalize -> Embed -> Enrich -> OpenCypher Writes"
echo "============================================================"

python -m src.ingest.write_graph

echo "============================================================"
echo "Ingestion completed successfully."
echo "============================================================"
