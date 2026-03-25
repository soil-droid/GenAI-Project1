from fastapi import FastAPI
from pydantic import BaseModel
from agent.agent import release_agent

app = FastAPI()

class Query(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_with_agent(query: Query):
    # Pass the user's prompt to the ADK agent
    response = release_agent.run(query.prompt)
    return {"response": response}