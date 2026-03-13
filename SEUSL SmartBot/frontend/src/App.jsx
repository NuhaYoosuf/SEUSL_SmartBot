import { useState, useRef, useEffect } from 'react'
import './App.css'

const QUICK_REPLIES = [
  "Who is the Vice Chancellor?",
  "What faculties are in SEUSL?",
  "How to apply for admission?",
  "Who is the Dean of FT?",
  "HOD of ICT in Faculty of Technology",
  "Contact details of SEUSL",
]

const formatTime = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <span /><span /><span />
    </div>
  )
}

function Message({ msg }) {
  return (
    <div className={`message-row ${msg.role}`}>
      {msg.role === 'bot' && <div className="avatar bot-avatar">🎓</div>}
      <div className="bubble-group">
        <div className={`bubble ${msg.role}`}>
          <p>{msg.text}</p>
          <span className="timestamp">{msg.time}</span>
        </div>
        {msg.sources && msg.sources.length > 0 && (
          <div className="sources">
            <span className="sources-label">📄 Sources:</span>
            {msg.sources.map((s, i) => (
              <span key={i} className="source-tag">
                {s.replace(/_/g, ' ').replace('.txt', '')}
              </span>
            ))}
          </div>
        )}
      </div>
      {msg.role === 'user' && <div className="avatar user-avatar">👤</div>}
    </div>
  )
}

function App() {
  const [messages, setMessages] = useState([{
    id: 1,
    role: 'bot',
    text: "Hello! I'm the SEUSL University Assistant. I can help you with information about faculties, programs, staff, admissions, and more. What would you like to know?",
    sources: [],
    time: formatTime()
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const q = (text !== undefined ? text : input).trim()
    if (!q || loading) return
    const userMsg = { id: Date.now(), role: 'user', text: q, sources: [], time: formatTime() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    inputRef.current?.focus()

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q })
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'bot',
        text: data.response,
        sources: data.sources || [],
        time: formatTime()
      }])
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'bot',
        text: 'Connection error. Please make sure the backend is running: uvicorn app:app --reload',
        sources: [],
        time: formatTime()
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`app${darkMode ? ' dark' : ''}`}>
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">🎓</div>
          <div>
            <h1 className="header-title">SEUSL Assistant</h1>
            <p className="header-sub">South Eastern University of Sri Lanka</p>
          </div>
        </div>
        <div className="header-actions">
          <span className="online-dot">● Online</span>
          <button className="icon-btn" onClick={() => setDarkMode(d => !d)} title="Toggle dark mode">
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="chat-body">
        {messages.map(msg => <Message key={msg.id} msg={msg} />)}
        {loading && (
          <div className="message-row bot">
            <div className="avatar bot-avatar">🎓</div>
            <div className="bubble bot loading-bubble"><TypingIndicator /></div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <div className="quick-replies">
        {QUICK_REPLIES.map((q, i) => (
          <button key={i} className="quick-btn" onClick={() => sendMessage(q)} disabled={loading}>
            {q}
          </button>
        ))}
      </div>

      <footer className="chat-footer">
        <div className="input-row">
          <label className="upload-btn" title="Upload document (coming soon)">📎
            <input type="file" hidden disabled />
          </label>
          <input
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Ask about SEUSL..."
            disabled={loading}
          />
          <button className="send-btn" onClick={() => sendMessage()} disabled={loading || !input.trim()}>➤</button>
        </div>
        <p className="footer-note">Powered by LLaMA 3 + RAG • SEUSL Knowledge Base</p>
      </footer>
    </div>
  )
}

export default App
