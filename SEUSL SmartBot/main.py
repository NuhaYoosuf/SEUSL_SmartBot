from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

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

print("=" * 60)
print("  Welcome to SEUSL University Chatbot")
print("  South Eastern University of Sri Lanka")
print("=" * 60)
print("  Type your question and press Enter.")
print("  Type 'q' to quit.")
print("=" * 60)

while True:
    print("\n")
    question = input("You: ").strip()
    if not question:
        continue
    if question.lower() == "q":
        print("Thank you for using SEUSL Chatbot. Goodbye!")
        break

    context_docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in context_docs])
    result = chain.invoke({"context": context, "question": question})
    print(f"\nSEUSL Bot: {result}")