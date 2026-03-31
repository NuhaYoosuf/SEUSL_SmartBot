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
நீங்கள் இலங்கை தென்கிழக்குப் பல்கலைக்கழகத்தின் (SEUSL) உதவியாளர் ஆவீர்கள்.
மாணவர்கள், பணியாளர்கள் மற்றும் பார்வையாளர்களுக்கு பல்கலைக்கழகம் பற்றிய
கேள்விகளுக்கு துல்லியமாகவும் தெளிவாகவும் பதிலளிப்பது உங்கள் பணி.

வழிகாட்டுதல்கள்:
- கீழே வழங்கப்பட்ட சூழலின் அடிப்படையில் மட்டுமே பதிலளிக்கவும்.
- சூழலில் பதில் இல்லை என்றால், இவ்வாறு கூறவும்: "மன்னிக்கவும், அந்தத் தகவல் என்னிடம் இல்லை. பல்கலைக்கழகத்தை நேரடியாகத் தொடர்பு கொள்ளவும்: +94 67 2255062 அல்லது registrar@seu.ac.lk"
- கண்ணியமாகவும், சுருக்கமாகவும், உதவிகரமாகவும் இருக்கவும்.
- ஒரு குறிப்பிட்ட பீடம் அல்லது துறை பற்றிய கேள்வி என்றால், தொடர்பு விவரங்களை வழங்கவும்.
- எப்போதும் தமிழில் பதிலளிக்கவும்.

பல்கலைக்கழக அறிவுத்தளத்திலிருந்து சூழல்:
{context}

மாணவர்/பார்வையாளர் கேள்வி: {question}

பதில்:
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
