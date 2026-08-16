# HydraDB Setup & Deployment Guide

This guide details the single-node local development setup (Primary Target) and optional Kubernetes EKS deployment for HydraDB ([`github.com/hydra-db/hydradb`](https://github.com/hydra-db/hydradb)).

---

## 1. Single-Node Dev Setup (Primary Target)

### Step 1: Create Local Auth Token File
In your repository root, generate `.graph_auth_token`:
```bash
printf '%s\n' 'local-development-token-32-bytes' > .graph_auth_token
```

*(Note: `.graph_auth_token` is listed in `.gitignore` to prevent secret commits).*

### Step 2: Launch Self-Hosted `graph-node` Process
Start the local HydraDB Rust process with `GRAPH_AUTH_TOKEN_FILE`:
```bash
GRAPH_AUTH_TOKEN_FILE=.graph_auth_token ./graph-node --port 8443
```

### Step 3: Verify HTTP Query Endpoint
Test query execution using `curl`:
```bash
curl -X POST http://127.0.0.1:8443/v1/graphs/default/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-development-token-32-bytes" \
  -d '{"query": "MATCH (n) RETURN n LIMIT 5"}'
```

Expected Response:
```json
{
  "status": "success",
  "results": [...]
}
```

---

## 2. Optional Kubernetes EKS Deployment

### Step 1: Create Kubernetes Secret
```bash
kubectl create secret generic hydradb-auth-token \
  --from-file=token=.graph_auth_token \
  --namespace=default
```

### Step 2: Install via Helm
```bash
helm upgrade --install hydradb ./charts/hydradb \
  -f ./charts/hydradb/values-eks.yaml \
  --namespace default
```

### Step 3: Verify Ingress / Cluster Query Endpoint
```bash
curl -X POST http://hydra-eks.internal.company.com/v1/graphs/default/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-development-token-32-bytes" \
  -d '{"query": "MATCH (n) RETURN n"}'
```
