# tools.py — ADK connection to the MCP Server
# adk_agent/tools.py
import sys
import os
from google_adk.mcp import MCPToolset
from google_adk.mcp.client import StdioServerParameters

def get_iss_toolset():
    # Get the absolute path to your MCP server script
    server_script = os.path.join(os.path.dirname(__file__), "iss_server.py")
    
    # Configure the client to run the python script via stdio
    server_params = StdioServerParameters(
        command=sys.executable, 
        args=[server_script]
    )
    
    tools = MCPToolset(connection_params=server_params)
    return tools