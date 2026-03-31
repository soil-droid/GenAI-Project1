"""
ISS Location MCP Server
Exposes a single tool — get_iss_location — via stdio transport.
The ADK agent launches this process as a subprocess and communicates over stdin/stdout.
"""

import requests
from mcp.server.fastmcp import FastMCP

# ── MCP Server Setup ──────────────────────────────────────────────────────────
mcp = FastMCP(
    name="ISS_Location_Server",
    instructions="Provides a tool to fetch the real-time location of the ISS.",
)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_iss_location() -> str:
    """Fetches the current real-time Latitude and Longitude of the International Space Station.

    Returns a string with the current latitude and longitude of the ISS,
    as well as the Unix timestamp of the observation.
    No arguments required — the ISS location is always live.
    """
    try:
        response = requests.get(
            "http://api.open-notify.org/iss-now.json",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        pos = data["iss_position"]
        timestamp = data.get("timestamp", "unknown")
        lat = pos["latitude"]
        lon = pos["longitude"]
        return (
            f"ISS Current Position:\n"
            f"  Latitude:  {lat}\n"
            f"  Longitude: {lon}\n"
            f"  Timestamp: {timestamp} (Unix epoch)\n"
            f"\n"
            f"Use these coordinates to determine what country, ocean, or region "
            f"the ISS is currently flying over."
        )
    except requests.RequestException as exc:
        return f"Error fetching ISS location from Open-Notify API: {exc}"


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run over standard input/output (stdio transport).
    # The ADK agent launches this script as a subprocess.
    mcp.run(transport="stdio")
