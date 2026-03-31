# 🛰️ ISS Orbit Agent

An AI agent that tracks the **International Space Station in real-time** using:

- **[Open-Notify API](http://api.open-notify.org/iss-now.json)** — free, no API key required
- **[Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)** — stdio transport
- **[Google ADK](https://google.github.io/adk-docs/)** — agent orchestration
- **[Gemini 2.0 Flash](https://ai.google.dev/gemini-api)** — LLM reasoning
- **[Cloud Run](https://cloud.google.com/run)** — serverless deployment

## Architecture

```
User (Browser)
     │  HTTP
     ▼
┌─────────────────────────────┐
│   ADK Agent  (FastAPI)      │  ← Single Cloud Run container
│   agent/main.py             │
│   Gemini 2.0 Flash          │
│            │ subprocess     │
│            ▼                │
│   MCP Server (stdio)        │  ← Spawned as subprocess
│   server/main.py            │
│   Open-Notify ISS API       │
└─────────────────────────────┘
                │  HTTP
                ▼
    api.open-notify.org
```

## Project Structure

```
iss-mcp-agent/
├── server/
│   ├── main.py           # MCP server — exposes get_iss_location tool
│   └── requirements.txt
├── agent/
│   ├── agent.py          # ADK root_agent definition
│   ├── main.py           # FastAPI server + chat web UI
│   ├── __init__.py
│   └── requirements.txt
├── Dockerfile            # Single container for Cloud Run
├── Dockerfile.mcp        # MCP server standalone image
├── Dockerfile.agent      # Agent standalone image
└── DEPLOY.md             # Step-by-step Cloud Run deployment guide
```

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r agent/requirements.txt -r server/requirements.txt

# 2. Set your Gemini API key
export GOOGLE_API_KEY="your-key-here"

# 3. Run the agent
python agent/main.py

# 4. Open http://localhost:8080 and ask:
#    "Where is the ISS right now?"
```

## Key Design

The agent demonstrates the **separation of concerns** pattern:

| Layer | File | Responsibility |
|-------|------|----------------|
| **Tool** | `server/main.py` | Fetches raw lat/lng from Open-Notify |
| **Agent** | `agent/agent.py` | Reasons about coordinates → geographic context |
| **Server** | `agent/main.py` | Serves the UI and REST API |

The MCP server is launched as a **stdio subprocess** — no network port needed for the MCP transport, making deployment simple with a single container.

## Deployment

See [DEPLOY.md](DEPLOY.md) for full Google Cloud Run deployment instructions.
