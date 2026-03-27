# 🌍 Where in the World is the ISS?
### A Real-Time Location Intelligence Agent Powered by MCP

**Hackathon Track:** Track 2 - Connect AI agents to real-world data and tools using Model Context Protocol (MCP).
**Live Demo (Cloud Run):** `[Insert Your Cloud Run URL Here]`

---

## 📊 Presentation / Slide Deck Guide

*This section maps directly to the required slides for the Track 2 hackathon submission.*

### [Slide 1] The Problem Statement: The AI Data Silo
Modern Large Language Models possess immense geographical and contextual knowledge, but they are frozen in time and disconnected from real-time events. 
* **The Challenge:** How do we give an AI agent access to live, constantly changing external data (like the location of a satellite traveling at 17,500 mph) without hardcoding fragile API connections directly into the AI's reasoning engine?
* **The Goal:** Build a secure, scalable, and standardized data-to-agent integration.

### [Slide 2] The Solution: "Where in the World is the ISS?"
We built a specialized Location Intelligence Agent that bridges real-time telemetry with AI reasoning.
* **What it does:** The user asks for the location of the International Space Station.
* **How it works:** The agent securely connects to a custom **Model Context Protocol (MCP)** server. It fetches raw telemetry (Latitude/Longitude) from the Open Notify API.
* **The AI Value-Add:** Instead of just returning numbers, the Gemini-powered agent uses its vast geographical knowledge to translate those coordinates into human-readable context (e.g., "It is currently flying over the Pacific Ocean, west of Chile").

### [Slide 3] Architecture & Tech Stack
Our architecture strictly separates **AI reasoning** from **tool execution**, ensuring a production-ready and secure environment.

| Layer | Technology | Function |
| :--- | :--- | :--- |
| **User Interface** | Google ADK Web UI | Provides a seamless, chat-based frontend for user interaction. |
| **Agent Orchestrator**| Google ADK + Gemini 3.1 Pro | Interprets intent, decides when to call tools, and synthesizes the final response. |
| **Integration Protocol**| Model Context Protocol (MCP) | The standardized bridge connecting the AI to external tools via `stdio`. |
| **Custom Data Server** | Python FastMCP | A lightweight, isolated server executing the data fetch tool. |
| **External Data** | Open Notify ISS API | The real-world data source providing live coordinates. |
| **Deployment** | Google Cloud Run | Serverless, containerized hosting for global accessibility. |

### [Slide 4] Why MCP? (The Core Innovation)
In traditional AI development, API keys and request logic are tangled inside the agent's code. By using **MCP**, we achieved:
1. **Separation of Concerns:** Our `iss_server.py` handles API requests. Our `agent.py` handles thinking. Neither needs to know how the other works.
2. **Security:** The agent never touches the external API directly; it only requests tool execution through the secure MCP standard.
3. **Scalability:** We can add 50 more tools to the MCP server tomorrow (like weather data, astronaut manifests, or orbital trajectories) without rewriting the core agent logic.

### [Slide 5] Real-World Action (Demo)
*When presenting, use this as a script for your live demo or screenshots.*

**User:** *"Where is the International Space Station right now?"*

**Behind the Scenes:**
1. Agent recognizes the need for live data.
2. Agent requests tool execution: `get_iss_location()` via MCP.
3. MCP Server queries `http://api.open-notify.org/iss-now.json`.
4. MCP Server returns: `{"latitude": -23.45, "longitude": -130.22}`.

**Agent's Final Response:** *"The International Space Station is currently located at Latitude -23.45 and Longitude -130.22. Based on these coordinates, the ISS is flying over the South Pacific Ocean, far off the western coast of South America!"*

---

## 🛠️ Repository Structure & Implementation

```text
iss_project/
├── requirements.txt      # Python dependencies (google-adk, mcp, requests)
├── Dockerfile            # Cloud Run container configuration
└── adk_agent/
    ├── iss_server.py     # The FastMCP Server (Data Layer)
    ├── tools.py          # The ADK/MCP Bridge (Integration Layer)
    └── agent.py          # The Gemini LlmAgent (Reasoning Layer)
