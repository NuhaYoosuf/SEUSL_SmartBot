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

Context from university knowledge base:
{context}

Student/Visitor Question: {question}

Answer (in Tamil):
""",
}

prompts = {lang: ChatPromptTemplate.from_template(t) for lang, t in TEMPLATES.items()}
chains = {lang: p | model for lang, p in prompts.items()}


class ChatRequest(BaseModel):
    message: str
    language: str = "en"


@app.get("/")
async def root():
    return {"status": "SEUSL Chatbot API is running", "version": "1.0.0"}


@app.post("/chat")
async def chat(request: ChatRequest):
    lang = request.language if request.language in chains else "en"
    context_docs = retriever.invoke(request.message)
    context = "\n\n".join([doc.page_content for doc in context_docs])
    sources = list({
        doc.metadata.get("source", "").replace("\\", "/").split("/")[-1]
        for doc in context_docs
        if doc.metadata.get("source")
    })
    response = chains[lang].invoke({"context": context, "question": request.message})
    return {"response": response, "sources": sources}
