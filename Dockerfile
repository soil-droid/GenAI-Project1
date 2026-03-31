# ─────────────────────────────────────────────────────────────────────────────
# ISS Orbit Agent — Single Container for Cloud Run
# Bundles: MCP server (server/) + ADK agent (agent/)
# The agent launches the MCP server as a subprocess (stdio transport).
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Install system deps (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install server dependencies first (layer caching)
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy and install agent dependencies
COPY agent/requirements.txt /app/agent/requirements.txt
RUN pip install --no-cache-dir -r /app/agent/requirements.txt

# Copy source code
COPY server/ /app/server/
COPY agent/  /app/agent/

# Expose Cloud Run port
EXPOSE 8080

# Run the FastAPI agent (which spawns the MCP server subprocess on demand)
CMD ["python", "-m", "agent.main"]