# WikiGuide Agent — Complete Deployment Guide
## ADK + Wikipedia MCP Server on Cloud Run

---

## Architecture

```
User Browser
     │
     ▼
┌─────────────────────────┐
│   ADK Agent (Cloud Run) │  ← Your submission URL
│   wiki-guide-agent      │
│   FastAPI + Gemini 2.0  │
└───────────┬─────────────┘
            │  MCP over SSE (HTTP)
            ▼
┌─────────────────────────┐
│  Wikipedia MCP Server   │
│  (Cloud Run)            │
│  FastMCP + wikipedia    │
└─────────────────────────┘
            │
            ▼
     Wikipedia API
```

---

## Step 0 — Prerequisites

```bash
# Verify gcloud is authenticated
gcloud auth list

# Set your project
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs (run once)
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

---

## Step 1 — Create Artifact Registry Repository

```bash
gcloud artifacts repositories create wiki-mcp-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="WikiGuide ADK Agent images"

# Authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Step 2 — Store Gemini API Key in Secret Manager

```bash
# Create the secret
echo -n "YOUR_GEMINI_API_KEY_HERE" | \
  gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy=automatic

# Verify it was created
gcloud secrets list
```
> Get your Gemini API key from: https://aistudio.google.com/app/apikey

---

## Step 3 — Deploy the Wikipedia MCP Server

### 3a. Build and push the MCP Server image

```bash
cd mcp-server

# Build image
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent/wiki-mcp-server:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent/wiki-mcp-server:latest
```

### 3b. Deploy MCP Server to Cloud Run

```bash
gcloud run deploy wiki-mcp-server \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent/wiki-mcp-server:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --port=8080
```

### 3c. Save the MCP Server URL

```bash
MCP_SERVER_URL=$(gcloud run services describe wiki-mcp-server \
  --region=us-central1 \
  --format='value(status.url)')

echo "MCP Server URL: $MCP_SERVER_URL"
# e.g. https://wiki-mcp-server-abc123-uc.a.run.app
```

### 3d. Test the MCP Server

```bash
# Health check — should return the SSE endpoint info
curl "$MCP_SERVER_URL/sse"
```

---

## Step 4 — Deploy the ADK Agent

### 4a. Build and push the Agent image

```bash
cd ../adk-agent

# Build image
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent/wiki-guide-agent:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent/wiki-guide-agent:latest
```

### 4b. Get your Cloud Run service account

```bash
# Cloud Run uses the default compute service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "Service Account: $SERVICE_ACCOUNT"
```

### 4c. Grant Secret Manager access to service account

```bash
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### 4d. Deploy ADK Agent to Cloud Run

```bash
gcloud run deploy wiki-guide-agent \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent/wiki-guide-agent:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --port=8080 \
  --set-env-vars="MCP_SERVER_URL=$MCP_SERVER_URL" \
  --set-secrets="GOOGLE_API_KEY=gemini-api-key:latest"
```

### 4e. Get your submission URL 🎉

```bash
AGENT_URL=$(gcloud run services describe wiki-guide-agent \
  --region=us-central1 \
  --format='value(status.url)')

echo "================================================"
echo "  SUBMISSION URL: $AGENT_URL"
echo "================================================"
```

---

## Step 5 — Test End-to-End

```bash
# Test the health endpoint
curl "$AGENT_URL/health"

# Test the chat API
curl -X POST "$AGENT_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is quantum computing?"}'

# Open the web UI in browser
echo "Open: $AGENT_URL"
```

---

## Step 6 — Viewing Logs (for debugging)

```bash
# MCP Server logs
gcloud run services logs read wiki-mcp-server \
  --region=us-central1 \
  --limit=50

# Agent logs
gcloud run services logs read wiki-guide-agent \
  --region=us-central1 \
  --limit=50

# Stream live logs
gcloud run services logs tail wiki-guide-agent \
  --region=us-central1
```

---

## Step 7 — Cleanup (after submission)

```bash
# Delete Cloud Run services
gcloud run services delete wiki-mcp-server --region=us-central1 --quiet
gcloud run services delete wiki-guide-agent --region=us-central1 --quiet

# Delete Artifact Registry images
gcloud artifacts repositories delete wiki-mcp-agent \
  --location=us-central1 \
  --quiet

# Delete the secret
gcloud secrets delete gemini-api-key --quiet
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GOOGLE_API_KEY not set` | Check secrets are mounted: `gcloud run services describe wiki-guide-agent --format=yaml` |
| MCP connection timeout | Ensure MCP Server is deployed with `--allow-unauthenticated` |
| Cold start slow | Set `--min-instances=1` on the agent service |
| 502 Bad Gateway | Check agent logs for startup errors |
| Wikipedia rate limit | Add `time.sleep(0.5)` between MCP tool calls in main.py |

---

## Quick Reference

```bash
# Useful aliases to add to your shell session
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export REGISTRY="us-central1-docker.pkg.dev/$PROJECT_ID/wiki-mcp-agent"
```
