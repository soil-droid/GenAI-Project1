import os
from google_adk import Agent
from google_adk.mcp import StdioServerParameters

# Ensure the GitHub token is provided via environment variables
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is missing!")

# Define the connection to the external GitHub MCP server
github_mcp_server = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN, "PATH": os.getenv("PATH")}
)

# Initialize the ADK Agent
github_agent = Agent(
    name="GitHub Issue Summarizer",
    instructions="""
    You are an expert developer assistant and project manager. 
    When a user asks about a GitHub repository, use your tools to fetch the repository's open issues.
    Do not return raw JSON. Instead, provide a clean, executive summary of the most pressing bugs or feature requests, categorizing them if possible.
    """,
    mcp_servers=[github_mcp_server], # Attach the MCP server to the agent
    model="gemini-3.1-pro"
)