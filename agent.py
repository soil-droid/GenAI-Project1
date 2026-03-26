from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

# 1. Configure the MCP Toolset
# This tells ADK to spin up your server.py and automatically ingest its tools
server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)
mcp_toolset = MCPToolset(server_parameters=server_params)

# 2. Define the ADK Agent
# The ADK Agent class handles the reasoning loop natively
rig_builder_agent = Agent(
    name="rig_builder_agent",
    model="gemini-2.5-flash",
    description="An expert PC building assistant.",
    instruction=(
        "You are an expert PC builder. When a user asks for a build, "
        "you MUST use your MCP tool to query the inventory database based on their budget and use case. "
        "Do not make up parts. Only suggest what the tool returns. "
        "Present the final results to the user in a friendly, conversational format."
    ),
    tools=[mcp_toolset]
)

# 3. Setup the ADK Runner and Session Management
# ADK uses a Runner to orchestrate the agent execution and keep track of chat history
session_service = InMemorySessionService()

# Create a default session for our web app
session = session_service.create_session(
    app_name="rig_builder_app",
    user_id="web_user",
    session_id="default_session"
)

runner = Runner(
    agent=rig_builder_agent,
    app_name="rig_builder_app",
    session_service=session_service
)

def run_adk_agent(user_prompt: str) -> str:
    """Executes the ADK Runner and extracts the final text response."""
    
    # Format the user input for the ADK Runner
    content = types.Content(
        role="user", 
        parts=[types.Part.from_text(text=user_prompt)]
    )
    
    # Execute the agent workflow
    events = runner.run(
        user_id="web_user",
        session_id="default_session",
        new_message=content
    )
    
    final_response = ""
    
    # The runner streams back events (thinking, tool calls, and final answers)
    for event in events:
        if event.content and event.content.parts and event.content.parts[0].text:
             final_response = event.content.parts[0].text
             
    return final_response

# Local testing block
if __name__ == "__main__":
    test_prompt = "I have exactly $2500 and I want to build a PC for 3D modeling. What parts should I get?"
    print(f"User: {test_prompt}\n")
    print("Agent is thinking...\n")
    response = run_adk_agent(test_prompt)
    print(f"Agent: {response}")