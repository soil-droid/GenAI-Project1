# Where in the World is the ISS? - MCP AI Agent

This repository contains a **Location Intelligence AI Agent** built for the **Track 2: Connect AI agents to real-world data and tools using Model Context Protocol (MCP)** hackathon challenge.

The agent leverages the **Google Agent Development Kit (ADK)** and the **Model Context Protocol (MCP)** to separate AI reasoning from tool execution. It connects to the live Open Notify ISS API to retrieve the current coordinates of the International Space Station and uses internal LLM geography knowledge to explain what country, ocean, or region it is currently flying over.

---

## Architecture & Tech Stack

The project follows a modular architecture, keeping the data-fetching logic strictly separated from the AI reasoning engine via a standard MCP interface.

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **LLM Reasoning** | Gemini 3.1 Pro | Interprets user intent, processes raw coordinates, and formulates a human-readable geographical response. |
| **Agent Framework** | Google ADK | Orchestrates the connection between the LLM and the tools, serving the built-in web UI. |
| **Tool Integration** | Model Context Protocol | Standardizes the communication between the agent and the external API script using `stdio`. |
| **Data Source** | Open Notify API | Provides real-time latitude and longitude data for the International Space Station. |
| **Deployment** | Google Cloud Run | Hosts the containerized application as a scalable, serverless endpoint. |

---

## Repository Structure

The project is organized to isolate the MCP server logic from the ADK agent configuration.

```text
iss_project/
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration for Cloud Run
└── adk_agent/
    ├── iss_server.py     # Custom FastMCP server fetching ISS coordinates
    ├── tools.py          # ADK connection bridging the agent and the MCP server
    └── agent.py          # Gemini LlmAgent definition and system instructions
