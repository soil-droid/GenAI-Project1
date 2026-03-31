# ISS Orbit Agent — Deployment Guide
## Single Container · Google Cloud Run

---

## Architecture

```
User Browser
     │
     ▼
┌─────────────────────────────────────┐
│   ISS Orbit Agent  (Cloud Run)      │  ← Single container, single service
│                                     │
│   agent/main.py  (FastAPI, :8080)   │
│   agent/agent.py (ADK + Gemini)     │
│            │                        │
│            │  subprocess (stdio)    │
│            ▼                        │
│   server/main.py (FastMCP)          │
│            │                        │
│            │  HTTP                  │
└────────────┼────────────────────────┘
             ▼
    api.open-notify.org  (ISS location — free, no key)
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
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com
```

---

## Step 1 — Create Artifact Registry Repository

```bash
gcloud artifacts repositories create iss-mcp-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="ISS Orbit Agent container images"

# Authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Step 2 — Store Gemini API Key in Secret Manager

```bash
# Create the secret (get your key from https://aistudio.google.com/app/apikey)
echo -n "YOUR_GEMINI_API_KEY_HERE" | \
  gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy=automatic

# Verify
gcloud secrets list
```

---

## Step 3 — Build & Push the Container Image

```bash
# From the project root (where Dockerfile lives)
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/iss-mcp-agent/iss-orbit-agent:latest .

docker push us-central1-docker.pkg.dev/$PROJECT_ID/iss-mcp-agent/iss-orbit-agent:latest
```

---

## Step 4 — Deploy to Cloud Run

### 4a. Get the default service account

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "Service Account: $SERVICE_ACCOUNT"
```

### 4b. Grant Secret Manager access

```bash
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### 4c. Deploy

```bash
gcloud run deploy iss-orbit-agent \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/iss-mcp-agent/iss-orbit-agent:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --port=8080 \
  --set-secrets="GOOGLE_API_KEY=gemini-api-key:latest"
```

### 4d. Get the submission URL 🎉

```bash
AGENT_URL=$(gcloud run services describe iss-orbit-agent \
  --region=us-central1 \
  --format='value(status.url)')

echo "==========================================="
echo "  SUBMISSION URL: $AGENT_URL"
echo "==========================================="
```

---

## Step 5 — Test End-to-End

```bash
# Health check
curl "$AGENT_URL/health"

# Ask where the ISS is
curl -X POST "$AGENT_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Where is the ISS right now?"}'

# Open the chat UI
echo "Open in browser: $AGENT_URL"
```

---

## Step 6 — View Logs

```bash
# View recent logs
gcloud run services logs read iss-orbit-agent \
  --region=us-central1 \
  --limit=50

# Stream live logs
gcloud run services logs tail iss-orbit-agent \
  --region=us-central1
```

---

## Step 7 — Cleanup (after submission)

```bash
# Delete Cloud Run service
gcloud run services delete iss-orbit-agent --region=us-central1 --quiet

# Delete Artifact Registry repo
gcloud artifacts repositories delete iss-mcp-agent \
  --location=us-central1 \
  --quiet

# Delete secret
gcloud secrets delete gemini-api-key --quiet
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GOOGLE_API_KEY not set` | Check secret is mounted: `gcloud run services describe iss-orbit-agent --format=yaml` |
| `ModuleNotFoundError: agent` | Ensure `CMD` runs from `/app` directory and `agent/__init__.py` exists |
| `StdioServerParameters` import error | Upgrade: `pip install --upgrade google-adk` |
| ISS API timeout | Open-Notify is a free service — retry after a few seconds |
| Cold start slow | Set `--min-instances=1` |

---

## Quick Reference

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export REGISTRY="us-central1-docker.pkg.dev/$PROJECT_ID/iss-mcp-agent"
export IMAGE="$REGISTRY/iss-orbit-agent:latest"
```
