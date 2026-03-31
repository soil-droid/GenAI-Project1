# WikiGuide Agent 🌐📚

An AI research agent built with **Google ADK** that connects to a **Wikipedia MCP Server** via Model Context Protocol (MCP) to answer questions with real, cited Wikipedia data.

## Architecture

| Component | Technology | Deployment |
|-----------|-----------|------------|
| AI Agent | Google ADK + Gemini 2.0 Flash | Cloud Run |
| MCP Server | FastMCP + Wikipedia API | Cloud Run |
| Transport | SSE (Server-Sent Events) | HTTPS |
| UI | FastAPI + Vanilla JS | Served by Agent |

## MCP Tools Exposed

- `search_wikipedia(query)` — Find relevant articles
- `get_article_summary(title)` — Get concise summary + URL
- `get_article_content(title, section?)` — Get full/sectioned content
- `get_related_topics(title)` — Find linked articles

## Project Structure

```
wiki-mcp-agent/
├── mcp-server/          # Wikipedia MCP Server
│   ├── main.py          # FastMCP tools
│   ├── requirements.txt
│   └── Dockerfile
├── adk-agent/           # ADK Agent + Web UI
│   ├── wiki_agent/
│   │   ├── __init__.py
│   │   └── agent.py     # ADK Agent definition
│   ├── main.py          # FastAPI server + HTML UI
│   ├── requirements.txt
│   └── Dockerfile
├── DEPLOY.md            # Complete deployment guide
└── README.md
```

## Quick Start

See [DEPLOY.md](./DEPLOY.md) for the full step-by-step deployment guide.

## Track

**Track 2** — Connect AI agents to real-world data and tools using Model Context Protocol (MCP)
