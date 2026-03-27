# agent.py — The Gemini Agent definition
# adk_agent/agent.py
from google_adk.agent import LlmAgent
import tools

# Load the custom MCP Toolset
iss_toolset = tools.get_iss_toolset()

# Define the Agent
print("Initializing ISS_Tracker_Agent...")
root_agent = LlmAgent(
    model='gemini-1.5-flash', 
    name='ISS_Tracker_Agent',
    instruction="""
    You are an enthusiastic geography and space expert. 
    When the user asks where the International Space Station is, use your tool to fetch its current latitude and longitude. 
    
    CRITICAL: Do not just reply with the coordinates. You must use your internal geographical knowledge to determine what country, city, state, or specific body of water corresponds to those coordinates. 
    
    Format your response nicely, mentioning the exact coordinates first, and then explaining what the ISS is currently flying over.
    """,
    tools=[iss_toolset]
)
print("Agent initialized successfully.")
