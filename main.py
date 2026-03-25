from fastapi import FastAPI
from pydantic import BaseModel
from agent import github_agent

app = FastAPI(title="GitHub Issue Summarizer API")

class QueryRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_with_agent(request: QueryRequest):
    # Pass the user's prompt directly to the ADK agent
    # Example prompt: "Summarize the 5 most recent issues in facebook/react"
    response = github_agent.run(request.prompt)
    
    return {
        "agent": "GitHub Issue Summarizer",
        "response": response
    }