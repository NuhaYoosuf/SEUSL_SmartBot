import os
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

SOURCE_DIRECTORIES = [
    "./data",
]
DB_LOCATION = "./seusl_vector_db_v7"
FORCE_REINDEX = os.getenv("SEUSL_FORCE_REINDEX", "").strip().lower() in {"1", "true", "yes"}


def load_all_documents():
    """Load all available text documents from configured source directories."""
    raw_documents = []

    for source_dir in SOURCE_DIRECTORIES:
        if not os.path.isdir(source_dir):
            print(f"Skipping missing source directory: {source_dir}")
            continue

        loader = DirectoryLoader(
            source_dir,
            glob="*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        docs = loader.load()
        print(f"Loaded {len(docs)} documents from {source_dir}")
        raw_documents.extend(docs)

    if not raw_documents:
        raise RuntimeError(
            "No knowledge-base text files were found in data sources: "
            + ", ".join(SOURCE_DIRECTORIES)
        )

    return raw_documents


if FORCE_REINDEX and os.path.exists(DB_LOCATION):
    print(f"Removing existing vector database for reindex: {DB_LOCATION}")
    try:
        shutil.rmtree(DB_LOCATION)
    except PermissionError:
        print(f"WARNING: Could not delete {DB_LOCATION} (files in use). Skipping reindex.")
        FORCE_REINDEX = False

add_documents = not os.path.exists(DB_LOCATION)

if add_documents:
    print("Loading and indexing university documents from all configured sources...")
    raw_documents = load_all_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30,
    )
    documents = splitter.split_documents(raw_documents)
    print(f"Prepared {len(documents)} chunks for embedding.")

vector_store = Chroma(
    collection_name="seusl_knowledge_base",
    persist_directory=DB_LOCATION,
    embedding_function=embeddings,
)

if add_documents:
    BATCH_SIZE = 10
    indexed = 0
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i + BATCH_SIZE]
        try:
            vector_store.add_documents(documents=batch)
            indexed += len(batch)
            print(f"  Indexed batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)")
        except Exception as e:
            # Fall back to one-by-one indexing for failed batches
            print(f"  Batch {i // BATCH_SIZE + 1} failed, trying individually...")
            for doc in batch:
                try:
                    vector_store.add_documents(documents=[doc])
                    indexed += 1
                except Exception:
                    preview = doc.page_content[:80].replace("\n", " ")
                    print(f"    ⚠ Skipped chunk: {preview}...")
    print(f"Indexed {indexed} document chunks into the knowledge base.")

retriever = vector_store.as_retriever(search_kwargs={"k": 8})
