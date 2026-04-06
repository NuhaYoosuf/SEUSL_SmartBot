import os
import re
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

SOURCE_DIRECTORIES = [
    "./data",
]
DB_LOCATION = "./seusl_vector_db_v8"
FORCE_REINDEX = os.getenv("SEUSL_FORCE_REINDEX", "").strip().lower() in {"1", "true", "yes"}

# Retrieval parameters
DENSE_K = 10       # top-k from dense (vector) retrieval
BM25_K = 10        # top-k from sparse (BM25) retrieval
FINAL_K = 5        # final number of documents returned after RRF
RRF_CONSTANT = 60  # standard RRF constant


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


# ---------------------------------------------------------------------------
# Tokenizer for BM25
# ---------------------------------------------------------------------------
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer for BM25."""
    return _WORD_RE.findall(text.lower())


# ---------------------------------------------------------------------------
# Build / load indices
# ---------------------------------------------------------------------------

if FORCE_REINDEX and os.path.exists(DB_LOCATION):
    print(f"Removing existing vector database for reindex: {DB_LOCATION}")
    try:
        shutil.rmtree(DB_LOCATION)
    except PermissionError:
        print(f"WARNING: Could not delete {DB_LOCATION} (files in use). Skipping reindex.")
        FORCE_REINDEX = False

add_documents = not os.path.exists(DB_LOCATION)

# Always load and chunk documents (needed for BM25 index which is in-memory)
print("Loading university documents for BM25 index...")
raw_documents = load_all_documents()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=30,
)
all_chunks: list[Document] = splitter.split_documents(raw_documents)
print(f"Prepared {len(all_chunks)} chunks.")

# --- Dense (vector) index --------------------------------------------------
vector_store = Chroma(
    collection_name="seusl_knowledge_base",
    persist_directory=DB_LOCATION,
    embedding_function=embeddings,
)

if add_documents:
    print("Indexing chunks into ChromaDB...")
    BATCH_SIZE = 10
    indexed = 0
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        try:
            vector_store.add_documents(documents=batch)
            indexed += len(batch)
            print(f"  Indexed batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)")
        except Exception as e:
            print(f"  Batch {i // BATCH_SIZE + 1} failed, trying individually...")
            for doc in batch:
                try:
                    vector_store.add_documents(documents=[doc])
                    indexed += 1
                except Exception:
                    preview = doc.page_content[:80].replace("\n", " ")
                    print(f"    ⚠ Skipped chunk: {preview}...")
    print(f"Indexed {indexed} document chunks into ChromaDB.")

dense_retriever = vector_store.as_retriever(search_kwargs={"k": DENSE_K})

# --- Sparse (BM25) index ---------------------------------------------------
_bm25_corpus = [_tokenize(doc.page_content) for doc in all_chunks]
bm25_index = BM25Okapi(_bm25_corpus)
print(f"Built BM25 index over {len(_bm25_corpus)} chunks.")


def _bm25_retrieve(query: str, k: int = BM25_K) -> list[Document]:
    """Retrieve top-k documents using BM25 scoring."""
    tokenized_query = _tokenize(query)
    scores = bm25_index.get_scores(tokenized_query)
    top_indices = scores.argsort()[-k:][::-1]
    return [all_chunks[i] for i in top_indices if scores[i] > 0]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------------------------

def _reciprocal_rank_fusion(
    ranked_lists: list[list[Document]],
    k: int = RRF_CONSTANT,
) -> list[Document]:
    """Fuse multiple ranked document lists using RRF.

    Score for each doc = sum over lists of  1 / (k + rank)
    where rank is 1-based position in each list.
    """
    # Use page_content as identity key (handles duplicates across retrievers)
    doc_scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list, start=1):
            key = doc.page_content
            doc_scores[key] = doc_scores.get(key, 0.0) + 1.0 / (k + rank)
            doc_map[key] = doc

    sorted_keys = sorted(doc_scores, key=lambda x: doc_scores[x], reverse=True)
    return [doc_map[k] for k in sorted_keys]


# ---------------------------------------------------------------------------
# Hybrid retriever (public interface used by app.py)
# ---------------------------------------------------------------------------

class HybridRetriever:
    """Combines dense (ChromaDB) and sparse (BM25) retrieval with RRF."""

    def invoke(self, query: str) -> list[Document]:
        dense_results = dense_retriever.invoke(query)
        bm25_results = _bm25_retrieve(query)
        fused = _reciprocal_rank_fusion([dense_results, bm25_results])
        return fused[:FINAL_K]


retriever = HybridRetriever()
print(f"Hybrid retriever ready (dense top-{DENSE_K} + BM25 top-{BM25_K} -> RRF top-{FINAL_K}).")
