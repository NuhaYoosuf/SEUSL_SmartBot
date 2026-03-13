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

template = """
You are a helpful and knowledgeable assistant for South Eastern University of Sri Lanka (SEUSL).
Your role is to assist students, staff, and visitors by answering questions about the university
accurately and clearly based on the provided context.

Guidelines:
- Answer only based on the context provided below.
- If the answer is not available in the context, say: "I'm sorry, I don't have that information. Please contact the university directly at +94 67 2255062 or email registrar@seu.ac.lk"
- Be polite, concise, and helpful.
- If a question is about a specific faculty or department, provide the relevant contact details when available.

Context from university knowledge base:
{context}

Student/Visitor Question: {question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


class ChatRequest(BaseModel):
    message: str


@app.get("/")
async def root():
    return {"status": "SEUSL Chatbot API is running", "version": "1.0.0"}


@app.post("/chat")
async def chat(request: ChatRequest):
    context_docs = retriever.invoke(request.message)
    context = "\n\n".join([doc.page_content for doc in context_docs])
    sources = list({
        doc.metadata.get("source", "").replace("\\", "/").split("/")[-1]
        for doc in context_docs
        if doc.metadata.get("source")
    })
    response = chain.invoke({"context": context, "question": request.message})
    return {"response": response, "sources": sources}
