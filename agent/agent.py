from google_adk import Agent
from toolbox_core import Toolset

# Load the tools defined in your YAML file
mcp_toolset = Toolset.from_yaml("tools.yaml", "my_bq_toolset")

# Initialize the ADK Agent (Ensure your GCP project/credentials are set in the environment)
release_agent = Agent(
    name="Cloud Release Tracker",
    instructions="You are a helpful IT assistant. Use the provided tools to look up recent Google Cloud release notes and summarize them for the user.",
    tools=mcp_toolset.get_tools(),
    model="gemini-3.1-pro" # Or your specified Gemini model
)