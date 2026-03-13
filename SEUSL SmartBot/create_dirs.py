import os

base = r'c:\Users\Nuha Yoosuf\Downloads\LocalAIAgentWithRAG-main\LocalAIAgentWithRAG-main'

# ── Create all directories ──────────────────────────────────────────────────
dirs = [
    os.path.join(base, 'scraper'),
    os.path.join(base, 'pdf_processor'),
    os.path.join(base, 'flask_frontend'),
    os.path.join(base, 'flask_frontend', 'templates'),
    os.path.join(base, 'flask_frontend', 'static'),
    os.path.join(base, 'scraped_data'),
    os.path.join(base, 'pdf_extracted_data'),
    os.path.join(base, 'seusl_pdfs'),
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f'Created dir : {d}')

# ── Write Flask app.py ──────────────────────────────────────────────────────
flask_app = r'''"""
SEUSL Chatbot — Flask Frontend
Serves the chat UI and proxies /chat requests to the FastAPI backend.

Usage:
    pip install flask requests
    python flask_frontend/app.py

Open: http://localhost:5000   (FastAPI backend must run on http://localhost:8000)
"""

from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)
BACKEND_URL = "http://localhost:8000/chat"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "No message provided"}), 400
    try:
        resp = requests.post(BACKEND_URL, json={"message": data["message"]}, timeout=120)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({
            "response": "Backend not reachable. Start FastAPI: uvicorn app:app --reload",
            "sources": []
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "response": "Request timed out. The LLM may still be loading.",
            "sources": []
        }), 504
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}", "sources": []}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  SEUSL Chatbot — Flask Frontend")
    print("  URL : http://localhost:5000")
    print("  API : http://localhost:8000  (FastAPI backend)")
    print("=" * 55)
    app.run(debug=True, port=5000)
'''

# ── Write CSS ───────────────────────────────────────────────────────────────
css = r''':root {
  --bg: #f0f4f8;
  --app-bg: #ffffff;
  --header-bg: #005f3b;
  --header-text: #ffffff;
  --user-bg: #005f3b;
  --user-text: #ffffff;
  --bot-bg: #f1f5f9;
  --bot-text: #1e293b;
  --input-bg: #f8fafc;
  --input-border: #cbd5e1;
  --footer-bg: #ffffff;
  --quick-bg: #e8f5e9;
  --quick-border: #a7d7b7;
  --quick-text: #005f3b;
  --source-bg: #f0fdf4;
  --source-border: #bbf7d0;
  --source-text: #166534;
  --text-muted: #64748b;
  --radius: 16px;
}
body.dark {
  --bg: #0f172a; --app-bg: #1e293b; --header-bg: #0a1628;
  --header-text: #f1f5f9; --user-bg: #2563eb; --user-text: #ffffff;
  --bot-bg: #334155; --bot-text: #e2e8f0; --input-bg: #1e293b;
  --input-border: #475569; --footer-bg: #1e293b; --quick-bg: #1e3a5f;
  --quick-border: #1d4ed8; --quick-text: #93c5fd; --source-bg: #1a3c2f;
  --source-border: #166534; --source-text: #86efac; --text-muted: #94a3b8;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;height:100vh;display:flex;justify-content:center;align-items:center;}
.app{width:100%;max-width:820px;height:100vh;display:flex;flex-direction:column;background:var(--app-bg);box-shadow:0 0 60px rgba(0,0,0,.15);transition:background .3s,color .3s;}
.header{background:var(--header-bg);color:var(--header-text);padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;}
.header-brand{display:flex;align-items:center;gap:12px;}
.header-logo{font-size:1.8rem;width:46px;height:46px;background:rgba(255,255,255,.15);border-radius:50%;display:flex;align-items:center;justify-content:center;}
.header-title{font-size:1.05rem;font-weight:700;margin:0 0 2px;}
.header-sub{font-size:.7rem;opacity:.75;}
.header-actions{display:flex;align-items:center;gap:12px;}
.online-dot{font-size:.72rem;color:#86efac;font-weight:500;}
.icon-btn{background:rgba(255,255,255,.15);border:none;border-radius:50%;width:36px;height:36px;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;transition:background .2s;}
.icon-btn:hover{background:rgba(255,255,255,.28);}
.chat-body{flex:1;overflow-y:auto;padding:20px 16px;display:flex;flex-direction:column;gap:14px;scroll-behavior:smooth;}
.chat-body::-webkit-scrollbar{width:5px;}
.chat-body::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px;}
.message-row{display:flex;align-items:flex-end;gap:8px;max-width:82%;animation:fadeUp .2s ease;}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.message-row.user{align-self:flex-end;flex-direction:row-reverse;}
.message-row.bot{align-self:flex-start;}
.avatar{width:33px;height:33px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.95rem;flex-shrink:0;}
.bot-avatar{background:#005f3b;}
.user-avatar{background:#e2e8f0;}
.bubble-group{display:flex;flex-direction:column;gap:5px;}
.bubble{padding:10px 14px;border-radius:var(--radius);line-height:1.55;font-size:.88rem;}
.bubble.bot{background:var(--bot-bg);color:var(--bot-text);border-bottom-left-radius:4px;}
.bubble.user{background:var(--user-bg);color:var(--user-text);border-bottom-right-radius:4px;}
.bubble p{margin:0;white-space:pre-wrap;word-break:break-word;}
.timestamp{display:block;font-size:.62rem;opacity:.55;margin-top:5px;text-align:right;}
.sources{display:flex;align-items:center;flex-wrap:wrap;gap:5px;margin-top:2px;}
.sources-label{font-size:.7rem;color:var(--text-muted);}
.source-tag{background:var(--source-bg);border:1px solid var(--source-border);color:var(--source-text);font-size:.68rem;padding:2px 9px;border-radius:12px;text-transform:capitalize;}
.loading-bubble{padding:14px 18px;min-width:62px;}
.typing-indicator{display:flex;gap:5px;align-items:center;}
.typing-indicator span{width:8px;height:8px;background:#94a3b8;border-radius:50%;animation:bounce 1.2s infinite ease-in-out;}
.typing-indicator span:nth-child(2){animation-delay:.2s;}
.typing-indicator span:nth-child(3){animation-delay:.4s;}
@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}
.quick-replies{padding:8px 14px;display:flex;gap:7px;overflow-x:auto;flex-shrink:0;background:var(--app-bg);border-top:1px solid var(--input-border);}
.quick-replies::-webkit-scrollbar{height:0;}
.quick-btn{white-space:nowrap;background:var(--quick-bg);border:1px solid var(--quick-border);color:var(--quick-text);padding:5px 13px;border-radius:20px;cursor:pointer;font-size:.76rem;font-weight:500;transition:filter .15s,transform .1s;flex-shrink:0;}
.quick-btn:hover:not(:disabled){filter:brightness(.9);transform:translateY(-1px);}
.quick-btn:disabled{opacity:.45;cursor:not-allowed;}
.chat-footer{padding:10px 14px 12px;background:var(--footer-bg);border-top:1px solid var(--input-border);flex-shrink:0;}
.input-row{display:flex;align-items:center;gap:8px;background:var(--input-bg);border:1.5px solid var(--input-border);border-radius:24px;padding:5px 6px 5px 14px;transition:border-color .2s;}
.input-row:focus-within{border-color:#005f3b;}
.upload-btn{cursor:not-allowed;font-size:1.05rem;opacity:.4;padding:4px;user-select:none;}
.chat-input{flex:1;border:none;background:transparent;outline:none;font-size:.88rem;color:var(--bot-text);padding:4px 0;}
.chat-input::placeholder{color:var(--text-muted);}
.send-btn{background:var(--user-bg);color:#fff;border:none;border-radius:50%;width:36px;height:36px;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;transition:opacity .15s,transform .1s;flex-shrink:0;}
.send-btn:hover:not(:disabled){transform:scale(1.08);}
.send-btn:disabled{opacity:.35;cursor:not-allowed;}
.footer-note{text-align:center;font-size:.62rem;color:var(--text-muted);margin-top:6px;}
'''

# ── Write HTML template ─────────────────────────────────────────────────────
html = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SEUSL Assistant</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}" />
</head>
<body>
<div class="app" id="app">

  <!-- Header -->
  <header class="header">
    <div class="header-brand">
      <div class="header-logo">🎓</div>
      <div>
        <h1 class="header-title">SEUSL Assistant</h1>
        <p class="header-sub">South Eastern University of Sri Lanka</p>
      </div>
    </div>
    <div class="header-actions">
      <span class="online-dot">● Online</span>
      <button class="icon-btn" id="darkToggle" title="Toggle dark mode">🌙</button>
    </div>
  </header>

  <!-- Chat messages -->
  <main class="chat-body" id="chatBody"></main>

  <!-- Quick replies -->
  <div class="quick-replies" id="quickReplies">
    <button class="quick-btn" onclick="sendMessage('Who is the Vice Chancellor?')">Who is the Vice Chancellor?</button>
    <button class="quick-btn" onclick="sendMessage('What faculties are in SEUSL?')">What faculties are in SEUSL?</button>
    <button class="quick-btn" onclick="sendMessage('How to apply for admission?')">How to apply for admission?</button>
    <button class="quick-btn" onclick="sendMessage('Who is the Dean of FT?')">Who is the Dean of FT?</button>
    <button class="quick-btn" onclick="sendMessage('HOD of ICT in Faculty of Technology')">HOD of ICT in Faculty of Technology</button>
    <button class="quick-btn" onclick="sendMessage('Contact details of SEUSL')">Contact details of SEUSL</button>
  </div>

  <!-- Footer / input -->
  <footer class="chat-footer">
    <div class="input-row">
      <span class="upload-btn" title="Upload (coming soon)">📎</span>
      <input
        class="chat-input"
        id="chatInput"
        type="text"
        placeholder="Ask about SEUSL..."
        autocomplete="off"
      />
      <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
    </div>
    <p class="footer-note">Powered by LLaMA 3 + RAG • SEUSL Knowledge Base</p>
  </footer>
</div>

<script>
  const chatBody   = document.getElementById('chatBody');
  const chatInput  = document.getElementById('chatInput');
  const sendBtn    = document.getElementById('sendBtn');
  const darkToggle = document.getElementById('darkToggle');
  const quickBtns  = document.querySelectorAll('.quick-btn');
  let   loading    = false;
  let   dark       = false;

  // ── Dark mode ──────────────────────────────────────────────────────────
  darkToggle.addEventListener('click', () => {
    dark = !dark;
    document.body.classList.toggle('dark', dark);
    darkToggle.textContent = dark ? '☀️' : '🌙';
  });

  // ── Enter key ──────────────────────────────────────────────────────────
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // ── Time helper ────────────────────────────────────────────────────────
  function now() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // ── Append a message bubble ────────────────────────────────────────────
  function appendMessage(role, text, sources) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatarHtml = role === 'bot'
      ? `<div class="avatar bot-avatar">🎓</div>`
      : `<div class="avatar user-avatar">👤</div>`;

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
      const tags = sources.map(s =>
        `<span class="source-tag">${s.replace(/_/g, ' ').replace('.txt', '')}</span>`
      ).join('');
      sourcesHtml = `<div class="sources"><span class="sources-label">📄 Sources:</span>${tags}</div>`;
    }

    const bubbleGroup = `
      <div class="bubble-group">
        <div class="bubble ${role}">
          <p>${escapeHtml(text)}</p>
          <span class="timestamp">${now()}</span>
        </div>
        ${sourcesHtml}
      </div>`;

    row.innerHTML = role === 'bot'
      ? avatarHtml + bubbleGroup
      : bubbleGroup + avatarHtml;

    chatBody.appendChild(row);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // ── Typing indicator ───────────────────────────────────────────────────
  function showTyping() {
    const row = document.createElement('div');
    row.className = 'message-row bot';
    row.id = 'typingRow';
    row.innerHTML = `
      <div class="avatar bot-avatar">🎓</div>
      <div class="bubble bot loading-bubble">
        <div class="typing-indicator"><span></span><span></span><span></span></div>
      </div>`;
    chatBody.appendChild(row);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  function hideTyping() {
    const row = document.getElementById('typingRow');
    if (row) row.remove();
  }

  // ── Set loading state ──────────────────────────────────────────────────
  function setLoading(state) {
    loading = state;
    sendBtn.disabled  = state;
    chatInput.disabled = state;
    quickBtns.forEach(b => b.disabled = state);
  }

  // ── Send message ───────────────────────────────────────────────────────
  async function sendMessage(text) {
    const q = (text !== undefined ? text : chatInput.value).trim();
    if (!q || loading) return;

    appendMessage('user', q, []);
    chatInput.value = '';
    setLoading(true);
    showTyping();

    try {
      const res  = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q })
      });
      const data = await res.json();
      hideTyping();
      appendMessage('bot', data.response || data.error, data.sources || []);
    } catch (err) {
      hideTyping();
      appendMessage('bot', 'Connection error. Make sure Flask and FastAPI are both running.', []);
    } finally {
      setLoading(false);
      chatInput.focus();
    }
  }

  // ── HTML escape helper ─────────────────────────────────────────────────
  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Initial greeting ───────────────────────────────────────────────────
  appendMessage('bot',
    "Hello! I'm the SEUSL University Assistant. I can help you with information about faculties, programs, staff, admissions, and more. What would you like to know?",
    []
  );
</script>
</body>
</html>
'''

# ── Write files ─────────────────────────────────────────────────────────────
files = {
    os.path.join(base, 'flask_frontend', 'app.py'):                    flask_app,
    os.path.join(base, 'flask_frontend', 'static', 'style.css'):       css,
    os.path.join(base, 'flask_frontend', 'templates', 'index.html'):   html,
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created file: {path}')

print('\ndone')
