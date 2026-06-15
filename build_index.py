"""
build_index.py

Milestone 4: turn our text chunks into a searchable vector index.

Big picture — three ideas:
  1. EMBEDDING: a model (all-MiniLM-L6-v2) reads each chunk and turns it into a
     list of 384 numbers (a "vector") that captures its meaning. Chunks about
     similar things end up with similar vectors.
  2. VECTOR STORE: we keep all those vectors in Chroma, a small local database
     built for "find the nearest vectors" searches.
  3. RETRIEVAL: at query time we embed the question the same way, then ask
     Chroma for the 5 chunks whose vectors are closest — those are the most
     relevant reviews to answer from.

We build the index once and save it to disk (./chroma_db) so later milestones
(generation) can just load it instead of re-embedding every time.

Run:  python3 build_index.py          # build the index
      python3 build_index.py "query"  # build (if needed) then test a query
"""

import sys

import chromadb
from chromadb.utils import embedding_functions

from chunk_documents import load_documents, chunk_all

# Where Chroma persists the index on disk, and what we name the collection.
DB_DIR = "chroma_db"
COLLECTION_NAME = "ucla_reviews"

# The embedding model from planning.md. 384-dim, runs locally, no API key.
EMBED_MODEL = "all-MiniLM-L6-v2"

# How many chunks to retrieve per query (planning.md Top-k = 5).
TOP_K = 5


def build_index() -> chromadb.Collection:
    """Embed all chunks and store them in a persistent Chroma collection.

    Returns the collection so the caller can immediately query it.
    """
    # 1. Load + chunk the raw documents (reusing Milestone 3 code).
    docs = load_documents()
    chunks = chunk_all(docs)
    print(f"Loaded {len(docs)} documents -> {len(chunks)} chunks")

    # 2. A persistent client writes the index to DB_DIR so it survives restarts.
    client = chromadb.PersistentClient(path=DB_DIR)

    # 3. Tell Chroma to embed text with all-MiniLM-L6-v2 (it downloads the model
    #    on first run, then caches it locally).
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

    # 4. Start fresh each build so re-running doesn't pile up duplicate chunks.
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )

    # 5. Add every chunk. Chroma embeds each "document" string for us. We attach
    #    the source filename as metadata so retrieved chunks keep attribution,
    #    and give each chunk a unique id.
    collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["filename"]} for c in chunks],
        ids=[f"chunk-{i}" for i in range(len(chunks))],
    )
    print(f"Indexed {collection.count()} chunks into '{COLLECTION_NAME}' ({DB_DIR}/)")
    return collection


def open_or_build_collection() -> chromadb.Collection:
    """Return the persisted Chroma collection, building it if it doesn't exist.

    Lets query.py / app.py reuse the saved index instead of re-embedding every
    time. If the collection is missing (first run), we build it once.
    """
    client = chromadb.PersistentClient(path=DB_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        return client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)
    # Not built yet — build it now.
    return build_index()


def retrieve(collection: chromadb.Collection, query: str, k: int = TOP_K):
    """Return the top-k chunks most relevant to `query`."""
    results = collection.query(query_texts=[query], n_results=k)
    # Chroma returns parallel lists; unpack the first (only) query's results.
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    return list(zip(docs, metas, dists))


if __name__ == "__main__":
    collection = build_index()

    # If a query was passed on the command line, run a quick retrieval demo.
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\n===== TOP {TOP_K} RESULTS for: {query!r} =====")
        for rank, (doc, meta, dist) in enumerate(retrieve(collection, query), 1):
            # Distance: lower = more similar. Show a short preview of each chunk.
            preview = " ".join(doc.split())[:200]
            print(f"\n#{rank}  (distance {dist:.3f}, source {meta['source']})")
            print(preview + ("..." if len(doc) > 200 else ""))
