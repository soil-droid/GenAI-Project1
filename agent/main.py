"""
ISS Orbit Agent — FastAPI Server
Serves the ADK agent via a REST API with a built-in space-themed chat UI.
"""

import asyncio
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

from agent.agent import root_agent

# ── App Lifecycle ──────────────────────────────────────────────────────────────

session_service = InMemorySessionService()
runner: Runner = None
APP_NAME = "iss_orbit_agent"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global runner
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    print("🛰️  ISS Orbit Agent started and ready.")
    yield
    print("👋 ISS Orbit Agent shutting down.")


# ── FastAPI App ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ISS Orbit Agent",
    description="An ADK-powered AI agent that tracks the ISS in real-time using MCP.",
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
        "agent": "ISS Orbit Agent",
        "model": "gemini-2.5-flash",
        "data_source": "api.open-notify.org",
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
        response_text = "I couldn't reach the ISS tracking system. Please try again."

    return ChatResponse(response=response_text, session_id=session_id)


# ── Web UI ────────────────────────────────────────────────────────────────────

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ISS Orbit Agent — Real-Time Space Tracker</title>
<meta name="description" content="Track the International Space Station in real-time with an AI agent powered by Google ADK and MCP."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:        #04060f;
    --surface:   #090d1a;
    --surface2:  #0e1428;
    --border:    #1a2240;
    --accent:    #4f8ef7;
    --accent2:   #a56ef5;
    --gold:      #f7c94f;
    --text:      #dde3f5;
    --text-muted:#6b7ba8;
    --user-bg:   #142060;
    --bot-bg:    #0a1030;
    --green:     #3dffa0;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  /* ── Starfield ── */
  body {
    font-family: 'Outfit', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
  }

  #stars {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background:
      radial-gradient(ellipse 80% 50% at 50% -10%, rgba(79,142,247,0.12) 0%, transparent 60%),
      radial-gradient(ellipse 40% 30% at 80% 80%, rgba(165,110,245,0.08) 0%, transparent 50%);
  }

  /* Animated star dots */
  .star {
    position: absolute;
    border-radius: 50%;
    background: white;
    animation: twinkle var(--d, 3s) ease-in-out infinite alternate;
    opacity: 0;
  }
  @keyframes twinkle {
    from { opacity: 0.1; transform: scale(1); }
    to   { opacity: 0.8; transform: scale(1.3); }
  }

  /* Orbiting ISS dot */
  .orbit-ring {
    position: fixed;
    width: 340px; height: 340px;
    border: 1px solid rgba(79,142,247,0.12);
    border-radius: 50%;
    top: -120px; right: -80px;
    animation: spin 40s linear infinite;
    pointer-events: none;
    z-index: 0;
  }
  .orbit-ring::after {
    content: '🛰️';
    position: absolute;
    top: -10px; left: 50%;
    transform: translateX(-50%);
    font-size: 18px;
    filter: drop-shadow(0 0 8px rgba(79,142,247,0.8));
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Header ── */
  header {
    position: relative; z-index: 10;
    background: rgba(9,13,26,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    flex-shrink: 0;
  }
  .logo {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 0 16px rgba(79,142,247,0.4);
  }
  .header-text h1 {
    font-size: 17px;
    font-weight: 700;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.02em;
  }
  .header-text p {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 2px;
    font-family: 'Space Mono', monospace;
  }
  .live-badge {
    margin-left: auto;
    display: flex; align-items: center; gap: 6px;
    background: rgba(61,255,160,0.08);
    border: 1px solid rgba(61,255,160,0.25);
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 11px;
    color: var(--green);
    font-family: 'Space Mono', monospace;
  }
  .live-dot {
    width: 7px; height: 7px;
    background: var(--green);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--green);
    animation: pulse 1.8s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.7); }
  }

  /* ── Chat window ── */
  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    position: relative; z-index: 10;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }

  /* ── Welcome screen ── */
  .welcome {
    text-align: center;
    padding: 36px 20px 20px;
    color: var(--text-muted);
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .welcome .iss-icon {
    font-size: 62px;
    margin-bottom: 16px;
    filter: drop-shadow(0 0 20px rgba(79,142,247,0.6));
    animation: float 4s ease-in-out infinite;
  }
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-10px); }
  }
  .welcome h2 {
    font-size: 26px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 10px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .welcome p {
    font-size: 14px;
    line-height: 1.7;
    max-width: 420px;
    margin-bottom: 26px;
    color: var(--text-muted);
  }
  .stat-bar {
    display: flex; gap: 16px; flex-wrap: wrap; justify-content: center;
    margin-bottom: 26px;
  }
  .stat {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 18px;
    text-align: center;
  }
  .stat .val {
    font-size: 18px;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: var(--gold);
  }
  .stat .lbl {
    font-size: 10px;
    color: var(--text-muted);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .suggestions {
    display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
  }
  .suggestion {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 9px 18px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text);
    font-family: 'Outfit', sans-serif;
  }
  .suggestion:hover {
    background: var(--surface2);
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: 0 0 12px rgba(79,142,247,0.15);
    transform: translateY(-1px);
  }

  /* ── Message bubbles ── */
  .msg { display: flex; gap: 10px; }
  .msg.user { flex-direction: row-reverse; align-self: flex-end; max-width: 75%; }
  .msg.bot  { align-self: flex-start; max-width: 82%; }

  .avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px;
    margin-top: 4px;
  }
  .msg.user .avatar { background: var(--user-bg); border: 1px solid rgba(79,142,247,0.3); }
  .msg.bot  .avatar {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    box-shadow: 0 0 10px rgba(79,142,247,0.35);
  }

  .bubble {
    padding: 13px 17px;
    border-radius: 18px;
    font-size: 14px;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg.user .bubble {
    background: var(--user-bg);
    border: 1px solid rgba(79,142,247,0.25);
    border-bottom-right-radius: 5px;
    color: #ccd6f6;
  }
  .msg.bot .bubble {
    background: var(--bot-bg);
    border: 1px solid var(--border);
    border-bottom-left-radius: 5px;
  }

  /* Bot bubble markdown styles */
  .bubble strong { color: var(--gold); }
  .bubble em     { color: var(--accent2); font-style: italic; }
  .bubble code   {
    background: rgba(79,142,247,0.12);
    padding: 2px 7px;
    border-radius: 5px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: var(--accent);
  }
  .bubble h1, .bubble h2, .bubble h3 {
    color: var(--accent);
    margin: 10px 0 4px;
    font-size: 14px;
  }
  .bubble ul, .bubble ol { padding-left: 20px; margin: 6px 0; }
  .bubble li { margin: 3px 0; }
  .bubble hr { border: none; border-top: 1px solid var(--border); margin: 10px 0; }
  .bubble a  { color: var(--accent2); text-decoration: none; }
  .bubble a:hover { text-decoration: underline; }

  /* Coords highlight */
  .coord-box {
    margin-top: 8px;
    background: rgba(79,142,247,0.07);
    border: 1px solid rgba(79,142,247,0.2);
    border-radius: 10px;
    padding: 8px 14px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: var(--accent);
  }

  /* Typing indicator */
  .typing-bubble { display: flex; gap: 5px; align-items: center; padding: 16px 20px; }
  .dot {
    width: 7px; height: 7px;
    background: var(--text-muted);
    border-radius: 50%;
    animation: bounce 1.3s infinite;
  }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30%            { transform: translateY(-7px); opacity: 1; }
  }

  /* ── Footer / Input ── */
  footer {
    position: relative; z-index: 10;
    background: rgba(9,13,26,0.95);
    backdrop-filter: blur(12px);
    border-top: 1px solid var(--border);
    padding: 14px 24px;
    flex-shrink: 0;
  }
  .input-row {
    display: flex; gap: 10px; align-items: flex-end;
    max-width: 860px; margin: 0 auto;
  }
  textarea {
    flex: 1;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 14px;
    color: var(--text);
    font-size: 14px;
    font-family: 'Outfit', sans-serif;
    padding: 12px 16px;
    resize: none;
    outline: none;
    min-height: 48px;
    max-height: 140px;
    line-height: 1.5;
    transition: border-color 0.25s, box-shadow 0.25s;
  }
  textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79,142,247,0.12);
  }
  textarea::placeholder { color: var(--text-muted); }

  #send-btn {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border: none;
    border-radius: 14px;
    color: white;
    cursor: pointer;
    padding: 0 22px;
    font-size: 18px;
    font-weight: 700;
    transition: opacity 0.2s, transform 0.12s, box-shadow 0.2s;
    flex-shrink: 0;
    height: 48px;
    box-shadow: 0 4px 16px rgba(79,142,247,0.3);
  }
  #send-btn:hover  { opacity: 0.88; box-shadow: 0 6px 20px rgba(79,142,247,0.45); }
  #send-btn:active { transform: scale(0.96); }
  #send-btn:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }

  .footer-hint {
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 8px;
    font-family: 'Space Mono', monospace;
  }
</style>
</head>
<body>

<!-- Background layer -->
<div id="stars"></div>
<div class="orbit-ring"></div>

<!-- Header -->
<header>
  <div class="logo">🛰️</div>
  <div class="header-text">
    <h1>ISS Orbit Agent</h1>
    <p>Real-time Space Tracker · Powered by Google ADK + MCP</p>
  </div>
  <div class="live-badge">
    <div class="live-dot"></div>
    LIVE TELEMETRY
  </div>
</header>

<!-- Chat -->
<div id="chat">
  <div class="welcome" id="welcome">
    <div class="iss-icon">🛰️</div>
    <h2>Where is the ISS right now?</h2>
    <p>
      I connect to real-time ISS telemetry via the Open-Notify API and use
      Gemini AI to tell you exactly what country or ocean the station is
      flying over — at this very moment.
    </p>
    <div class="stat-bar">
      <div class="stat">
        <div class="val">~28,000</div>
        <div class="lbl">km/h orbital speed</div>
      </div>
      <div class="stat">
        <div class="val">~408</div>
        <div class="lbl">km altitude</div>
      </div>
      <div class="stat">
        <div class="val">90 min</div>
        <div class="lbl">per orbit</div>
      </div>
    </div>
    <div class="suggestions">
      <div class="suggestion" onclick="sendSuggestion(this)">🌍 Where is the ISS right now?</div>
      <div class="suggestion" onclick="sendSuggestion(this)">🗺️ What country is the ISS over?</div>
      <div class="suggestion" onclick="sendSuggestion(this)">🌊 Is the ISS over an ocean?</div>
      <div class="suggestion" onclick="sendSuggestion(this)">📍 Give me the exact ISS coordinates</div>
    </div>
  </div>
</div>

<!-- Input -->
<footer>
  <div class="input-row">
    <textarea
      id="input"
      placeholder="Ask about the ISS location... (Enter to send)"
      rows="1"
      autofocus
    ></textarea>
    <button id="send-btn" onclick="sendMessage()">➤</button>
  </div>
  <p class="footer-hint">Google ADK · Open-Notify API · MCP stdio · Cloud Run</p>
</footer>

<script>
  // ── Starfield generation ──────────────────────────────────────────────────
  const starsEl = document.getElementById('stars');
  for (let i = 0; i < 180; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    const size = Math.random() * 2.2 + 0.5;
    s.style.cssText = `
      width:${size}px; height:${size}px;
      top:${Math.random()*100}%;
      left:${Math.random()*100}%;
      --d:${(Math.random()*3+2).toFixed(1)}s;
      animation-delay:${(Math.random()*4).toFixed(1)}s;
    `;
    starsEl.appendChild(s);
  }

  // ── Chat logic ────────────────────────────────────────────────────────────
  let sessionId = null;
  const chat    = document.getElementById('chat');
  const input   = document.getElementById('input');
  const sendBtn = document.getElementById('send-btn');

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 140) + 'px';
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  function sendSuggestion(el) {
    input.value = el.textContent.replace(/^[^a-zA-Z]+/, '').trim();
    sendMessage();
  }

  function appendMessage(role, html) {
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();

    const msg    = document.createElement('div');
    msg.className = `msg ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? '👤' : '🛰️';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (role === 'bot') {
      bubble.innerHTML = formatMarkdown(html);
    } else {
      bubble.textContent = html;
    }

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
  }

  function showTyping() {
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();

    const msg = document.createElement('div');
    msg.className = 'msg bot';
    msg.id = 'typing-msg';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '🛰️';

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
      .replace(/^# (.+)$/gm,  '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^### (.+)$/gm,'<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g,     '<em>$1</em>')
      .replace(/`([^`]+)`/g,     '<code>$1</code>')
      .replace(/^---$/gm,        '<hr>')
      .replace(/^[•\-] (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>(\n|$))+/g, '<ul>$&</ul>')
      .replace(/(https?:\/\/[^\s<]+)/g,
               '<a href="$1" target="_blank">$1</a>')
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
      const res  = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      });

      const data = await res.json();
      sessionId  = data.session_id;
      removeTyping();

      if (res.ok) {
        appendMessage('bot', data.response);
      } else {
        appendMessage('bot', '⚠️ Error: ' + (data.detail || 'Something went wrong.'));
      }
    } catch (err) {
      removeTyping();
      appendMessage('bot', '⚠️ Network error. Is the agent running?');
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
