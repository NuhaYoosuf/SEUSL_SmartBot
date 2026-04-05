import uuid
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

app = FastAPI(title="SEUSL Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = OllamaLLM(model="llama3")

# ---------------------------------------------------------------------------
# Conversational Memory — sliding window (last 5 turns per session)
# ---------------------------------------------------------------------------
MEMORY_WINDOW = 5          # number of Q-A turns to retain
SESSION_TTL = 3600         # expire inactive sessions after 1 hour

# session_id -> {"history": [(question, answer), ...], "last_active": float}
session_store: dict[str, dict] = {}


def _get_history(session_id: str) -> list[tuple[str, str]]:
    """Return the conversation history list for a session (may be empty)."""
    if session_id in session_store:
        session_store[session_id]["last_active"] = time.time()
        return session_store[session_id]["history"]
    return []


def _add_turn(session_id: str, question: str, answer: str):
    """Append a turn and enforce the sliding window limit."""
    if session_id not in session_store:
        session_store[session_id] = {"history": [], "last_active": time.time()}
    session_store[session_id]["history"].append((question, answer))
    session_store[session_id]["history"] = session_store[session_id]["history"][-MEMORY_WINDOW:]
    session_store[session_id]["last_active"] = time.time()


def _cleanup_sessions():
    """Remove sessions idle longer than SESSION_TTL."""
    now = time.time()
    expired = [sid for sid, d in session_store.items() if now - d["last_active"] > SESSION_TTL]
    for sid in expired:
        del session_store[sid]


def _format_history(history: list[tuple[str, str]]) -> str:
    """Render chat history into a plain-text block for the prompt."""
    if not history:
        return "No previous conversation."
    lines = []
    for q, a in history:
        lines.append(f"Student: {q}")
        lines.append(f"Assistant: {a}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt templates (with chat_history slot)
# ---------------------------------------------------------------------------
TEMPLATES = {
    "en": """
You are a helpful and knowledgeable assistant for South Eastern University of Sri Lanka (SEUSL).
Your role is to assist students, staff, and visitors by answering questions about the university
accurately and clearly based on the provided context.

Guidelines:
- Answer only based on the context provided below.
- If the answer is not available in the context, say: "I'm sorry, I don't have that information. Please contact the university directly at +94 67 2255062 or email registrar@seu.ac.lk"
- Be polite, concise, and helpful.
- If a question is about a specific faculty or department, provide the relevant contact details when available.
- Always respond in English.
- Use the previous conversation to understand follow-up questions. If the student refers to something mentioned earlier (e.g. "tell me more", "what about that", "and the fees?"), use the chat history to resolve what they mean.

Previous conversation:
{chat_history}

Context from university knowledge base:
{context}

Student/Visitor Question: {question}

Answer:
""",
    "ta": """
You are a helpful and knowledgeable assistant for South Eastern University of Sri Lanka (SEUSL).
Your role is to assist students, staff, and visitors by answering questions about the university
accurately and clearly based on the provided context.

Guidelines:
- Answer only based on the context provided below.
- If the answer is not available in the context, say in Tamil: "மன்னிக்கவும், அந்தத் தகவல் என்னிடம் இல்லை. தயவுசெய்து பல்கலைக்கழகத்தை நேரடியாகத் தொடர்பு கொள்ளுங்கள்: +94 67 2255062 அல்லது registrar@seu.ac.lk"
- Be polite, concise, and helpful.
- If a question is about a specific faculty or department, provide the relevant contact details when available.
- IMPORTANT: You MUST always respond entirely in Tamil language (தமிழ்). Translate all English information from the context into Tamil before responding. Keep proper nouns, names, email addresses, phone numbers, and abbreviations (like SEUSL, ICT, FT) in English.
- Use the previous conversation to understand follow-up questions. If the student refers to something mentioned earlier, use the chat history to resolve what they mean.

Previous conversation:
{chat_history}

Context from university knowledge base:
{context}

Student/Visitor Question: {question}

Answer (in Tamil):
""",
}

prompts = {lang: ChatPromptTemplate.from_template(t) for lang, t in TEMPLATES.items()}
chains = {lang: p | model for lang, p in prompts.items()}

# Query reformulation prompt — rewrites follow-up questions into standalone queries
CONDENSE_TEMPLATE = """Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question that includes all necessary context.
If the follow-up question is already standalone and clear, return it unchanged.
Only output the rephrased question, nothing else.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone Question:"""

condense_prompt = ChatPromptTemplate.from_template(CONDENSE_TEMPLATE)
condense_chain = condense_prompt | model


class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    session_id: str = ""


@app.get("/")
async def root():
    return {"status": "SEUSL Chatbot API is running", "version": "1.0.0"}


@app.post("/chat")
async def chat(request: ChatRequest):
    _cleanup_sessions()

    session_id = request.session_id or str(uuid.uuid4())
    lang = request.language if request.language in chains else "en"

    history = _get_history(session_id)
    chat_history = _format_history(history)

    # If there is conversation history, reformulate the question for better retrieval
    search_query = request.message
    if history:
        search_query = condense_chain.invoke({
            "chat_history": chat_history,
            "question": request.message,
        }).strip()

    context_docs = retriever.invoke(search_query)
    context = "\n\n".join([doc.page_content for doc in context_docs])
    sources = list({
        doc.metadata.get("source", "").replace("\\", "/").split("/")[-1]
        for doc in context_docs
        if doc.metadata.get("source")
    })

    response = chains[lang].invoke({
        "context": context,
        "question": request.message,
        "chat_history": chat_history,
    })

    _add_turn(session_id, request.message, response)

    return {"response": response, "sources": sources, "session_id": session_id}
