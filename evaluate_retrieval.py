"""
evaluate_retrieval.py

Milestone 4 verification: run the 5 evaluation questions from planning.md
through the retriever and check whether the expected professor shows up in the
top-5 retrieved chunks.

This tests RETRIEVAL only (does the right context come back?). Judging the
final worded answer is Milestone 5, once generation is wired up.

Run:  python evaluate_retrieval.py
"""

import chromadb
from chromadb.utils import embedding_functions

from build_index import DB_DIR, COLLECTION_NAME, EMBED_MODEL, TOP_K, retrieve

# Each eval question paired with the professor we expect to see in the results.
# (Questions come straight from planning.md's Evaluation Plan table.)
EVAL = [
    ("Which CS 31 professor do students most recommend, and why?", "Bruce Huang"),
    ("How do students describe Howard Stahl's CS 32 difficulty and grading "
     "compared to Smallberg/Nachenberg?", "Howard Stahl"),
    ("What do reviews say about Paul Eggert's CS 33 class?", "Paul Eggert"),
    ("What are students' main complaints about Glenn Reinman's CS 33 course?",
     "Glenn Reinman"),
    ("According to reviews, how do students feel about David Smallberg despite "
     "his lecture style?", "David Smallberg"),
]


def open_collection() -> chromadb.Collection:
    """Open the already-built persistent Chroma collection (no re-embedding)."""
    client = chromadb.PersistentClient(path=DB_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)


if __name__ == "__main__":
    collection = open_collection()

    passed = 0
    for i, (question, expected_prof) in enumerate(EVAL, 1):
        results = retrieve(collection, question, k=TOP_K)

        # Find the rank (1-based) at which the expected professor first appears.
        rank = None
        for r, (doc, meta, dist) in enumerate(results, 1):
            if expected_prof in doc:
                rank = r
                break

        hit = rank is not None
        passed += hit
        status = f"PASS (rank {rank})" if hit else "MISS"
        print(f"Q{i}: {status} — expected '{expected_prof}'")
        print(f"    {question}")
        # Show which professors actually came back, for inspection.
        names = []
        for doc, meta, dist in results:
            line = next((l for l in doc.splitlines()
                         if l.startswith("Professor:")), "Professor: ?")
            names.append(line.replace("Professor: ", ""))
        print(f"    top-{TOP_K}: {names}\n")

    print(f"===== {passed}/{len(EVAL)} questions retrieved the expected professor =====")
