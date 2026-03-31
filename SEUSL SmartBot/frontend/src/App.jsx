import { useState, useRef, useEffect } from 'react'
import './App.css'

const UI_TEXT = {
  en: {
    title: "SEUSL Assistant",
    subtitle: "South Eastern University of Sri Lanka",
    welcome: "Hello! I'm the SEUSL University Assistant. I can help you with information about faculties, programs, staff, admissions, and more. What would you like to know?",
    placeholder: "Ask about SEUSL...",
    online: "● Online",
    footerNote: "Powered by LLaMA 3 + RAG • SEUSL Knowledge Base",
    connectionError: "Connection error. Please make sure the backend is running: uvicorn app:app --reload",
    sourcesLabel: "📄 Sources:",
    quickReplies: [
      "Who is the Vice Chancellor?",
      "What faculties are in SEUSL?",
      "How to apply for admission?",
      "Who is the Dean of FT?",
      "HOD of ICT in Faculty of Technology",
      "Contact details of SEUSL",
    ],
  },
  ta: {
    title: "SEUSL உதவியாளர்",
    subtitle: "இலங்கை தென்கிழக்குப் பல்கலைக்கழகம்",
    welcome: "வணக்கம்! நான் SEUSL பல்கலைக்கழக உதவியாளர். பீடங்கள், படிப்புகள், பணியாளர்கள், சேர்க்கை மற்றும் பல விடயங்கள் பற்றி உங்களுக்கு உதவ முடியும். நீங்கள் என்ன அறிய விரும்புகிறீர்கள்?",
    placeholder: "SEUSL பற்றி கேளுங்கள்...",
    online: "● இணைப்பில்",
    footerNote: "LLaMA 3 + RAG மூலம் இயக்கப்படுகிறது • SEUSL அறிவுத்தளம்",
    connectionError: "இணைப்புப் பிழை. பின்புலம் இயங்குகிறதா என்பதை உறுதிப்படுத்தவும்: uvicorn app:app --reload",
    sourcesLabel: "📄 ஆதாரங்கள்:",
    quickReplies: [
      "துணைவேந்தர் யார்?",
      "SEUSL இல் என்ன பீடங்கள் உள்ளன?",
      "சேர்க்கைக்கு எவ்வாறு விண்ணப்பிப்பது?",
      "FT இன் பீடாதிபதி யார்?",
      "தொழில்நுட்ப பீடத்தில் ICT துறைத்தலைவர்",
      "SEUSL தொடர்பு விவரங்கள்",
    ],
  },
}

const formatTime = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <span /><span /><span />
    </div>
  )
}

function Message({ msg, sourcesLabel }) {
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
            <span className="sources-label">{sourcesLabel}</span>
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
  const [language, setLanguage] = useState('en')
  const t = UI_TEXT[language]
  const [messages, setMessages] = useState([{
    id: 1,
    role: 'bot',
    text: UI_TEXT.en.welcome,
    sources: [],
    time: formatTime()
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'ta' : 'en'
    setLanguage(newLang)
    setMessages([{
      id: Date.now(),
      role: 'bot',
      text: UI_TEXT[newLang].welcome,
      sources: [],
      time: formatTime()
    }])
  }

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
        body: JSON.stringify({ message: q, language })
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
        text: t.connectionError,
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
            <h1 className="header-title">{t.title}</h1>
            <p className="header-sub">{t.subtitle}</p>
          </div>
        </div>
        <div className="header-actions">
          <span className="online-dot">{t.online}</span>
          <button className="lang-btn" onClick={toggleLanguage} title="Switch language">
            {language === 'en' ? 'தமிழ்' : 'English'}
          </button>
          <button className="icon-btn" onClick={() => setDarkMode(d => !d)} title="Toggle dark mode">
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="chat-body">
        {messages.map(msg => <Message key={msg.id} msg={msg} sourcesLabel={t.sourcesLabel} />)}
        {loading && (
          <div className="message-row bot">
            <div className="avatar bot-avatar">🎓</div>
            <div className="bubble bot loading-bubble"><TypingIndicator /></div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <div className="quick-replies">
        {t.quickReplies.map((q, i) => (
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
            placeholder={t.placeholder}
            disabled={loading}
          />
          <button className="send-btn" onClick={() => sendMessage()} disabled={loading || !input.trim()}>➤</button>
        </div>
        <p className="footer-note">{t.footerNote}</p>
      </footer>
    </div>
  )
}

export default App
