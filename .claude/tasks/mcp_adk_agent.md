# Plan: MCP ADK Agent Project

## Overview
The goal is to build an AI agent using the Model Context Protocol (MCP) to connect to an external tool (SQLite DB returning PC build suggestions), retrieve information, and use it in its response. The result will be deployed to Cloud Run using Google ADK.

## Step-by-Step Implementation Plan

### 1. Codebase Fixes
- **`app.py`**: Fix the unresolved import issue. The `agent.py` exports `run_adk_agent`, but `app.py` imports `run_agent`. We will change line 4 in `app.py` to `from agent import run_adk_agent`.
- **`requirements.txt`**: Ensure that all required packages for ADK and FastMCP are included. The file currently has `mcp`, `google-genai`, `flask`, `gunicorn`. It needs to include `google-adk` (which is standard for Google-ADK lab).

### 2. Local Testing
- Start the Flask app locally and submit a prompt (e.g., "I have $2500 and want a 3D modeling PC").
- Ensure the ADK agent successfully spawns the MCP server via standard IO (`stdio`), fetches data from the SQLite DB tool `suggest_pc_build`, and returns a formulated response to the UI.

### 3. Cloud Run Deployment
- Ensure `Dockerfile` is correctly structured (it currently looks good: Python 3.10 slim, installs requirements, exposes 8080, and runs `gunicorn ... app:app`).
- Because stdio MCP requires the `server.py` script to be run by the `agent.py` process, they both need to exist in the same container. The current `Dockerfile` copies all files, which fits this requirement.
- Provide a clear script or set of commands (`gcloud run deploy ...`) for deploying the container to Google Cloud Run. We can also provide a `deploy.ps1` script if you want to deploy it directly from this machine (assuming `gcloud` is authenticated).

## Reasoning
The provided boilerplate already effectively satisfies the "What You Must Build" requirements:
- ADK is used (`google.adk.agents.Agent`).
- MCP is used (`FastMCP` for server, `MCPToolset` for client).
- Retrieves structured data (queries PC inventory).
- Generates a response using this data.

All that is left is to clean up the bugs, verify its functionality, and prepare for submission via a Cloud Run link.

## Minimum Viable Product (MVP)
The MVP is the working Flask app serving the rig builder AI that consults the SQLite DB MCP server via ADK without any errors, successfully deployed on Cloud Run.

## Implementation Updates
Detailed descriptions of the changes made:
1. **app.py**: Changed `from agent import run_agent` to `from agent import run_adk_agent` to fix the export boundary.
2. **requirements.txt**: Added `google-adk` to satisfy the missing library requirement for running the project. 
3. **agent.py (MCPToolset)**: Changed `server_parameters` argument to `connection_params` for `MCPToolset` initialization, as required by the latest ADK specification. 
4. **agent.py (sys.executable)**: Updated the MCP Standard IO tool connection command from plain `"python"` to `sys.executable`. This ensures that `server.py` runs inside the active python virtual environment and has access to FastMCP.
5. **agent.py (Runner Session)**: Removed the explicit synchronous call to `session_service.create_session(...)` (which was causing an unawaited coroutine error) and passed `auto_create_session=True` directly into the `Runner` instance.
6. **Deployment Script**: Created `deploy.ps1` to easily automate the Google Cloud Run source deployment and securely inject the `GEMINI_API_KEY`.

---
Please let me know if you approve of this plan or if you would like to make any modifications before I proceed to the implementation!
