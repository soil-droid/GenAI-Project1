"""
WikiGuide Agent — FastAPI Server
Serves the ADK agent via a REST API with a built-in chat web interface.
"""

import os
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from wiki_agent.agent import root_agent

# ── App Lifecycle ──────────────────────────────────────────────────────────────

session_service = InMemorySessionService()
runner: Runner = None
APP_NAME = "wiki_guide"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global runner
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    print(f"✅ WikiGuide Agent started. MCP Server: {os.environ.get('MCP_SERVER_URL')}")
    yield
    print("👋 WikiGuide Agent shutting down.")


# ── FastAPI App ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="WikiGuide Agent",
    description="An ADK-powered AI agent that answers questions using Wikipedia via MCP.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": "WikiGuide",
        "mcp_server": os.environ.get("MCP_SERVER_URL", "not set"),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not runner:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    session_id = req.session_id or str(uuid.uuid4())
    user_id = "web_user"

    # Get or create session
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    # Run agent and collect final response
    response_text = ""
    new_message = Content(parts=[Part(text=req.message)], role="user")

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        if event.is_final_response() and event.response:
            for part in event.response.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text

    if not response_text:
        response_text = "I couldn't generate a response. Please try again."

    return ChatResponse(response=response_text, session_id=session_id)


# ── Web UI ────────────────────────────────────────────────────────────────────

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>WikiGuide — AI Research Agent</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d2e;
    --surface2: #252840;
    --border: #2e3250;
    --accent: #6c8ef5;
    --accent2: #a78bfa;
    --text: #e2e4f0;
    --text-muted: #8b90b8;
    --user-bubble: #2a3a7c;
    --bot-bubble: #1e2235;
    --success: #4ade80;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Header */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }
  .logo {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }
  header h1 { font-size: 18px; font-weight: 600; }
  header p { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
  .status-dot {
    width: 8px; height: 8px;
    background: var(--success);
    border-radius: 50%;
    margin-left: auto;
    box-shadow: 0 0 6px var(--success);
  }

  /* Chat window */
  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }

  /* Welcome message */
  .welcome {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
  }
  .welcome .icon { font-size: 48px; margin-bottom: 16px; }
  .welcome h2 { font-size: 22px; color: var(--text); margin-bottom: 8px; }
  .welcome p { font-size: 14px; line-height: 1.6; max-width: 400px; margin: 0 auto 24px; }
  .suggestions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
  .suggestion {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text);
  }
  .suggestion:hover {
    background: var(--surface2);
    border-color: var(--accent);
    color: var(--accent);
  }

  /* Message bubbles */
  .msg { display: flex; gap: 10px; max-width: 820px; }
  .msg.user { flex-direction: row-reverse; align-self: flex-end; }
  .msg.bot { align-self: flex-start; }

  .avatar {
    width: 32px; height: 32px; border-radius: 50%;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    margin-top: 4px;
  }
  .msg.user .avatar { background: var(--user-bubble); }
  .msg.bot .avatar {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
  }

  .bubble {
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.65;
    max-width: 680px;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg.user .bubble {
    background: var(--user-bubble);
    border-bottom-right-radius: 4px;
  }
  .msg.bot .bubble {
    background: var(--bot-bubble);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
  }

  /* Markdown-like formatting inside bot bubbles */
  .bubble h1, .bubble h2, .bubble h3 {
    color: var(--accent);
    margin: 10px 0 4px;
    font-size: 14px;
  }
  .bubble strong { color: #c4caff; }
  .bubble a { color: var(--accent); text-decoration: none; }
  .bubble a:hover { text-decoration: underline; }
  .bubble code {
    background: rgba(108,142,245,0.15);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
  }
  .bubble hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 10px 0;
  }
  .bubble ul, .bubble ol {
    padding-left: 20px;
    margin: 6px 0;
  }
  .bubble li { margin: 3px 0; }
  .bubble .url-link {
    display: inline-flex; align-items: center; gap: 4px;
    color: var(--accent2); font-size: 12px;
  }

  /* Typing indicator */
  .typing-bubble {
    display: flex; gap: 5px; align-items: center;
    padding: 14px 18px;
  }
  .dot {
    width: 7px; height: 7px;
    background: var(--text-muted);
    border-radius: 50%;
    animation: bounce 1.3s infinite;
  }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
    30% { transform: translateY(-6px); opacity: 1; }
  }

  /* Input area */
  footer {
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 16px 24px;
    flex-shrink: 0;
  }
  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    max-width: 860px;
    margin: 0 auto;
  }
  textarea {
    flex: 1;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text);
    font-size: 14px;
    font-family: inherit;
    padding: 12px 16px;
    resize: none;
    outline: none;
    min-height: 46px;
    max-height: 140px;
    line-height: 1.5;
    transition: border-color 0.2s;
  }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--text-muted); }

  #send-btn {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border: none;
    border-radius: 12px;
    color: white;
    cursor: pointer;
    padding: 12px 20px;
    font-size: 16px;
    font-weight: 600;
    transition: opacity 0.2s, transform 0.1s;
    flex-shrink: 0;
    height: 46px;
  }
  #send-btn:hover { opacity: 0.9; }
  #send-btn:active { transform: scale(0.97); }
  #send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .footer-hint {
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 8px;
  }
</style>
</head>
<body>

<header>
  <div class="logo">🌐</div>
  <div>
    <h1>WikiGuide</h1>
    <p>AI Research Agent · Powered by ADK + Wikipedia MCP</p>
  </div>
  <div class="status-dot"></div>
</header>

<div id="chat">
  <div class="welcome" id="welcome">
    <div class="icon">📚</div>
    <h2>Ask me anything</h2>
    <p>I search Wikipedia in real-time using Model Context Protocol to give you accurate, cited answers.</p>
    <div class="suggestions">
      <div class="suggestion" onclick="sendSuggestion(this)">What is quantum computing?</div>
      <div class="suggestion" onclick="sendSuggestion(this)">History of the Indian Space Program</div>
      <div class="suggestion" onclick="sendSuggestion(this)">How does photosynthesis work?</div>
      <div class="suggestion" onclick="sendSuggestion(this)">Tell me about the Renaissance</div>
      <div class="suggestion" onclick="sendSuggestion(this)">What is machine learning?</div>
    </div>
  </div>
</div>

<footer>
  <div class="input-row">
    <textarea
      id="input"
      placeholder="Ask anything — I'll look it up on Wikipedia..."
      rows="1"
      autofocus
    ></textarea>
    <button id="send-btn" onclick="sendMessage()">➤</button>
  </div>
  <p class="footer-hint">Built with Google ADK · Wikipedia MCP · Cloud Run</p>
</footer>

<script>
  let sessionId = null;
  const chat = document.getElementById('chat');
  const input = document.getElementById('input');
  const sendBtn = document.getElementById('send-btn');

  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 140) + 'px';
  });

  // Send on Enter (Shift+Enter for new line)
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  function sendSuggestion(el) {
    input.value = el.textContent;
    sendMessage();
  }

  function appendMessage(role, text) {
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();

    const msg = document.createElement('div');
    msg.className = `msg ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (role === 'bot') {
      bubble.innerHTML = formatMarkdown(text);
    } else {
      bubble.textContent = text;
    }

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
    return bubble;
  }

  function showTyping() {
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();

    const msg = document.createElement('div');
    msg.className = 'msg bot';
    msg.id = 'typing-msg';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'bubble typing-bubble';
    bubble.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
  }

  function removeTyping() {
    const t = document.getElementById('typing-msg');
    if (t) t.remove();
  }

  function formatMarkdown(text) {
    return text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^---$/gm, '<hr>')
      .replace(/^[•\-] (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>(\n|$))+/g, '<ul>$&</ul>')
      .replace(/(https?:\/\/[^\s<]+)/g,
        '<a href="$1" target="_blank" class="url-link">🔗 $1</a>')
      .replace(/\n/g, '<br>');
  }

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    appendMessage('user', msg);
    showTyping();

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      });

      const data = await res.json();
      sessionId = data.session_id;
      removeTyping();

      if (res.ok) {
        appendMessage('bot', data.response);
      } else {
        appendMessage('bot', '⚠️ Error: ' + (data.detail || 'Something went wrong.'));
      }
    } catch (err) {
      removeTyping();
      appendMessage('bot', '⚠️ Network error. Please check your connection.');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML_CONTENT)


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
