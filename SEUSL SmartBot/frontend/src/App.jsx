import { useState, useRef, useEffect } from 'react'
import './App.css'

const UI_TEXT = {
  en: {
    title: "SEUSL SmartBot",
    subtitle: "South Eastern University of Sri Lanka",
    welcome: "Hello! I'm the SEUSL SmartBot — your intelligent university assistant. Ask me anything about faculties, programs, admissions, staff, campus facilities, and more.",
    placeholder: "Type your question here...",
    online: "Online",
    footerNote: "Powered by LLaMA 3 + RAG — SEUSL Knowledge Base",
    connectionError: "Unable to connect to the server. Please ensure the backend is running.",
    sourcesLabel: "Sources",
    historyTitle: "Chat History",
    noHistory: "No conversations yet",
    deleteAll: "Clear All",
    today: "Today",
    yesterday: "Yesterday",
    older: "Older",
    welcomeCards: [
      { icon: "🏛️", title: "University Info", desc: "Faculties, departments & programs" },
      { icon: "📋", title: "Admissions", desc: "How to apply & requirements" },
      { icon: "👥", title: "Staff Directory", desc: "Deans, HODs & contacts" },
      { icon: "🏠", title: "Campus Life", desc: "Hostel, facilities & services" },
    ],
    quickReplies: [
      "What faculties are in SEUSL?",
      "Who is the Vice Chancellor?",
      "How to apply for admission?",
      "Who is the Dean of FT?",
      "Contact details of SEUSL",
      "Tell me about hostel facilities",
    ],
  },
  ta: {
    title: "SEUSL SmartBot",
    subtitle: "தென்கிழக்குப் பல்கலைக்கழகம், இலங்கை",
    welcome: "வணக்கம்! நான் SEUSL SmartBot — உங்கள் நுண்ணறிவு பல்கலைக்கழக உதவியாளர். பீடங்கள், கற்கை நெறிகள், மாணவர் அனுமதி, ஊழியர்கள், வளாக வசதிகள் பற்றி கேளுங்கள்.",
    placeholder: "உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யுங்கள்...",
    online: "ஆன்லைன்",
    footerNote: "LLaMA 3 + RAG — SEUSL தரவுத்தளம்",
    connectionError: "சேவையக இணைப்புப் பிழை. Backend சேவையகம் இயங்குகிறதா என்பதை உறுதிப்படுத்தவும்.",
    sourcesLabel: "மூலங்கள்",
    historyTitle: "உரையாடல் வரலாறு",
    noHistory: "இதுவரை உரையாடல்கள் இல்லை",
    deleteAll: "அனைத்தையும் அழி",
    today: "இன்று",
    yesterday: "நேற்று",
    older: "பழையவை",
    welcomeCards: [
      { icon: "🏛️", title: "பல்கலைக்கழக தகவல்", desc: "பீடங்கள், துறைகள் & நிகழ்ச்சிகள்" },
      { icon: "📋", title: "மாணவர் அனுமதி", desc: "விண்ணப்பிக்கும் முறை & தேவைகள்" },
      { icon: "👥", title: "ஊழியர் அடைவு", desc: "பீடாதிபதிகள், தலைவர்கள் & தொடர்புகள்" },
      { icon: "🏠", title: "வளாக வாழ்க்கை", desc: "விடுதி, வசதிகள் & சேவைகள்" },
    ],
    quickReplies: [
      "SEUSL இல் எத்தனை பீடங்கள் உள்ளன?",
      "துணைவேந்தர் யார்?",
      "மாணவர் அனுமதிக்கு எவ்வாறு விண்ணப்பிப்பது?",
      "தொழில்நுட்ப பீடத்தின் பீடாதிபதி யார்?",
      "SEUSL தொடர்பு விபரங்கள்",
      "விடுதி வசதிகள் பற்றி சொல்லுங்கள்",
    ],
  },
}

const formatTime = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

function TypingIndicator() {
  return (
    <div className="typing-dots">
      <span /><span /><span />
    </div>
  )
}

function Message({ msg, sourcesLabel }) {
  return (
    <div className={`msg-row ${msg.role}`}>
      {msg.role === 'bot' && (
        <div className="msg-avatar bot-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
            <path d="M6 12v5c3 3 9 3 12 0v-5" />
          </svg>
        </div>
      )}
      <div className="msg-content">
        <div className={`msg-bubble ${msg.role}`}>
          <p>{msg.text}</p>
        </div>
        <div className="msg-meta">
          <span className="msg-time">{msg.time}</span>
          {msg.sources && msg.sources.length > 0 && (
            <div className="msg-sources">
              <span className="sources-icon">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </span>
              <span className="sources-label">{sourcesLabel}:</span>
              {msg.sources.map((s, i) => (
                <span key={i} className="source-chip">
                  {s.replace(/_/g, ' ').replace('.txt', '')}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      {msg.role === 'user' && (
        <div className="msg-avatar user-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      )}
    </div>
  )
}

function WelcomeScreen({ t, onQuickReply, loading }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
          <path d="M6 12v5c3 3 9 3 12 0v-5" />
        </svg>
      </div>
      <h2 className="welcome-title">{t.title}</h2>
      <p className="welcome-text">{t.welcome}</p>
      <div className="welcome-cards">
        {t.welcomeCards.map((card, i) => (
          <div key={i} className="welcome-card">
            <span className="card-icon">{card.icon}</span>
            <span className="card-title">{card.title}</span>
            <span className="card-desc">{card.desc}</span>
          </div>
        ))}
      </div>
      <div className="welcome-suggestions">
        <p className="suggestions-label">Try asking:</p>
        <div className="suggestions-list">
          {t.quickReplies.slice(0, 4).map((q, i) => (
            <button key={i} className="suggestion-btn" onClick={() => onQuickReply(q)} disabled={loading}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── localStorage helpers ──
const HISTORY_KEY = 'seusl_chat_history'

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []
  } catch { return [] }
}
function saveHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

function getDateGroup(timestamp, t) {
  const d = new Date(timestamp)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1)
  if (d >= today) return t.today
  if (d >= yesterday) return t.yesterday
  return t.older
}

// ── Sidebar component ──
function Sidebar({ open, onClose, history, onSelect, onDelete, onDeleteAll, t }) {
  // group by date
  const grouped = {}
  history.forEach(entry => {
    const group = getDateGroup(entry.createdAt, t)
    if (!grouped[group]) grouped[group] = []
    grouped[group].push(entry)
  })
  const groupOrder = [t.today, t.yesterday, t.older]

  return (
    <>
      <div className={`sidebar-overlay${open ? ' visible' : ''}`} onClick={onClose} />
      <aside className={`sidebar${open ? ' open' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">{t.historyTitle}</h2>
          <button className="sidebar-close" onClick={onClose}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {history.length === 0 ? (
          <div className="sidebar-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <p>{t.noHistory}</p>
          </div>
        ) : (
          <div className="sidebar-list">
            {groupOrder.map(group => grouped[group] && (
              <div key={group} className="sidebar-group">
                <span className="sidebar-group-label">{group}</span>
                {grouped[group].map(entry => (
                  <button key={entry.sessionId} className="sidebar-item" onClick={() => { onSelect(entry); onClose() }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    <div className="sidebar-item-content">
                      <span className="sidebar-item-title">{entry.title}</span>
                      <span className="sidebar-item-time">{new Date(entry.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <button className="sidebar-item-delete" onClick={e => { e.stopPropagation(); onDelete(entry.sessionId) }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                  </button>
                ))}
              </div>
            ))}
            <button className="sidebar-clear-all" onClick={onDeleteAll}>{t.deleteAll}</button>
          </div>
        )}
      </aside>
    </>
  )
}

function App() {
  const [language, setLanguage] = useState('en')
  const t = UI_TEXT[language]
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID())
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatHistory, setChatHistory] = useState(loadHistory)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  const hasMessages = messages.length > 0

  // Persist history whenever it changes
  useEffect(() => { saveHistory(chatHistory) }, [chatHistory])

  // Save current conversation to history (if it has messages)
  const saveCurrentChat = () => {
    if (messages.length === 0) return
    const firstUserMsg = messages.find(m => m.role === 'user')
    const title = firstUserMsg ? firstUserMsg.text.slice(0, 60) : 'New conversation'
    setChatHistory(prev => {
      const existing = prev.findIndex(h => h.sessionId === sessionId)
      const entry = {
        sessionId,
        title,
        createdAt: existing >= 0 ? prev[existing].createdAt : Date.now(),
        updatedAt: Date.now(),
        messages,
        language,
      }
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = entry
        return updated
      }
      return [entry, ...prev]
    })
  }

  // Auto-save current conversation when messages change (after first message)
  useEffect(() => {
    if (messages.length > 0) saveCurrentChat()
  }, [messages])

  const loadChat = (entry) => {
    setMessages(entry.messages)
    setSessionId(entry.sessionId)
    setLanguage(entry.language || 'en')
  }

  const deleteChat = (sid) => {
    setChatHistory(prev => prev.filter(h => h.sessionId !== sid))
    if (sid === sessionId) {
      setMessages([])
      setSessionId(crypto.randomUUID())
    }
  }

  const deleteAllHistory = () => {
    setChatHistory([])
    setMessages([])
    setSessionId(crypto.randomUUID())
  }

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'ta' : 'en'
    setLanguage(newLang)
    setMessages([])
    setSessionId(crypto.randomUUID())
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
        body: JSON.stringify({ message: q, language, session_id: sessionId })
      })
      const data = await res.json()
      if (data.session_id) setSessionId(data.session_id)
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

  const clearChat = () => {
    setMessages([])
    setSessionId(crypto.randomUUID())
  }

  return (
    <div className={`app${darkMode ? ' dark' : ''}`}>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        history={chatHistory}
        onSelect={loadChat}
        onDelete={deleteChat}
        onDeleteAll={deleteAllHistory}
        t={t}
      />

      <header className="header">
        <div className="header-left">
          <button className="header-btn" onClick={() => setSidebarOpen(true)} title="Chat history">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <div className="header-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
              <path d="M6 12v5c3 3 9 3 12 0v-5" />
            </svg>
          </div>
          <div className="header-info">
            <h1 className="header-title">{t.title}</h1>
            <div className="header-status">
              <span className="status-dot" />
              <span className="status-text">{t.online}</span>
            </div>
          </div>
        </div>
        <div className="header-right">
          {hasMessages && (
            <button className="header-btn" onClick={clearChat} title="New chat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          )}
          <button className="header-btn lang" onClick={toggleLanguage} title="Switch language">
            {language === 'en' ? 'தமிழ்' : 'EN'}
          </button>
          <button className="header-btn" onClick={() => setDarkMode(d => !d)} title="Toggle theme">
            {darkMode ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            )}
          </button>
        </div>
      </header>

      <main className="chat-area">
        {!hasMessages ? (
          <WelcomeScreen t={t} onQuickReply={sendMessage} loading={loading} />
        ) : (
          <div className="messages-container">
            {messages.map(msg => (
              <Message key={msg.id} msg={msg} sourcesLabel={t.sourcesLabel} />
            ))}
            {loading && (
              <div className="msg-row bot">
                <div className="msg-avatar bot-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                    <path d="M6 12v5c3 3 9 3 12 0v-5" />
                  </svg>
                </div>
                <div className="msg-content">
                  <div className="msg-bubble bot typing">
                    <TypingIndicator />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </main>

      {hasMessages && (
        <div className="quick-bar">
          {t.quickReplies.map((q, i) => (
            <button key={i} className="quick-chip" onClick={() => sendMessage(q)} disabled={loading}>
              {q}
            </button>
          ))}
        </div>
      )}

      <footer className="input-footer">
        <div className="input-container">
          <input
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={t.placeholder}
            disabled={loading}
          />
          <button
            className={`send-btn${input.trim() ? ' active' : ''}`}
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="footer-text">{t.footerNote}</p>
      </footer>
    </div>
  )
}

export default App
