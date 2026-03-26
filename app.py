import os
import asyncio
from flask import Flask, request, render_template_string
from agent import run_adk_agent

app = Flask(__name__)

# A very simple, clean UI for the judges to interact with
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Rig Builder Agent</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
        input[type="text"] { width: 100%; padding: 10px; margin-bottom: 10px; }
        button { padding: 10px 20px; background-color: #007bff; color: white; border: none; cursor: pointer; }
        .response { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin-top: 20px; white-space: pre-wrap;}
    </style>
</head>
<body>
    <h2>💻 Rig Builder AI (MCP + ADK)</h2>
    <p>Ask the agent to suggest a PC build. It will securely query the inventory MCP server.</p>
    
    <form method="POST" action="/ask">
        <input type="text" name="prompt" value="I have exactly $2500 and I want to build a PC for 3D modeling. What parts should I get?" required>
        <button type="submit">Ask Agent</button>
    </form>

    {% if response %}
        <div class="response">
            <strong>Agent Response:</strong><br><br>
            {{ response }}
        </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@@app.route("/ask", methods=["POST"])
def ask():
    user_prompt = request.form.get("prompt")
    # Call the ADK agent directly (no asyncio needed)
    agent_response = run_adk_agent(user_prompt)
    return render_template_string(HTML_TEMPLATE, response=agent_response)

if __name__ == "__main__":
    # Cloud Run expects the app to listen on the PORT environment variable (default 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)