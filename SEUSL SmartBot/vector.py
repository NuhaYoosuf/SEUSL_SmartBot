from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "./seusl_vector_db_v5"
add_documents = not os.path.exists(db_location)

if add_documents:
    print("Loading and indexing university documents...")
    loader = DirectoryLoader(
        "./data",
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    raw_documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    documents = splitter.split_documents(raw_documents)

vector_store = Chroma(
    collection_name="seusl_knowledge_base",
    persist_directory=db_location,
    embedding_function=embeddings
)

if add_documents:
    vector_store.add_documents(documents=documents)
    print(f"Indexed {len(documents)} document chunks into the knowledge base.")

retriever = vector_store.as_retriever(
    search_kwargs={"k": 8}
)