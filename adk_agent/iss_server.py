# iss_server.py — Custom MCP Server for ISS data
# adk_agent/iss_server.py
import requests
from mcp.server.fastmcp import FastMCP

# Initialize a lightweight MCP Server
mcp = FastMCP("ISS Tracker")

@mcp.tool()
def get_iss_location() -> str:
    """Get the current latitude and longitude of the International Space Station."""
    url = "http://api.open-notify.org/iss-now.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        lat = data["iss_position"]["latitude"]
        lon = data["iss_position"]["longitude"]
        return f"The ISS is currently located at Latitude: {lat}, Longitude: {lon}"
    else:
        return "Error: Could not retrieve the ISS location at this time."

if __name__ == "__main__":
    # Runs the server using standard input/output (stdio)
    mcp.run()