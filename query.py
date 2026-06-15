"""
query.py

Milestone 5 (generation): turn a user question into a GROUNDED answer.

Pipeline for one question:
  1. retrieve  — get the top-5 most relevant chunks from Chroma (Milestone 4)
  2. build prompt — stuff those chunks into a context block and instruct the
     LLM to answer ONLY from that context
  3. generate  — call Groq's llama-3.3-70b-versatile
  4. attribute — append the source filenames PROGRAMMATICALLY (from the
     retrieved chunks' metadata), so attribution can't be hallucinated

The grounding lives in SYSTEM_PROMPT: it tells the model to answer only from the
provided context and to say "I don't have enough information on that." when the
context doesn't cover the question.

Requires GROQ_API_KEY in a .env file (never hardcode it).
"""

import os

from dotenv import load_dotenv
from groq import Groq

from build_index import open_or_build_collection, retrieve, TOP_K

# Load GROQ_API_KEY (and anything else) from .env into the environment.
load_dotenv()

# Groq's free-tier, OpenAI-compatible 70B model (assignment's recommended default).
LLM_MODEL = "llama-3.3-70b-versatile"

# The grounding contract. This is the single most important piece of Milestone 5:
# it must ENFORCE answering from context, not merely suggest it.
SYSTEM_PROMPT = """You are a helpful assistant that answers questions about UCLA \
computer science courses and professors using ONLY the student reviews provided \
in the context below.

Rules you must follow:
1. Answer using ONLY the information in the provided context. Do not use any \
outside or prior knowledge about these courses or professors.
2. If the context does not contain enough information to answer the question, \
reply with exactly: "I don't have enough information on that."
3. Do not invent professors, ratings, quotes, or facts that are not in the context.
4. When you state a fact, ground it in what the reviews actually say.

Context is a set of review chunks, each beginning with its Source URL, Course, \
and Professor."""

# How the user turn is formatted: context block first, then the question.
USER_TEMPLATE = """Context:
{context}

Question: {question}

Answer using only the context above."""


def _format_context(results: list[tuple]) -> str:
    """Join retrieved chunks into one context string the LLM can read."""
    blocks = []
    for i, (doc, meta, dist) in enumerate(results, 1):
        blocks.append(f"[Chunk {i} — {meta['source']}]\n{doc}")
    return "\n\n".join(blocks)


def ask(question: str, k: int = TOP_K) -> dict:
    """Answer `question` grounded in retrieved chunks.

    Returns a dict: {"answer": str, "sources": list[str]}.
    The sources list is built from chunk metadata, NOT from the LLM, so source
    attribution is guaranteed rather than left to the model.
    """
    # 1. Retrieve the most relevant chunks.
    collection = open_or_build_collection()
    results = retrieve(collection, question, k=k)

    # 2. Build the grounded prompt.
    context = _format_context(results)
    user_message = USER_TEMPLATE.format(context=context, question=question)

    # 3. Generate. temperature=0 keeps the model close to the context.
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # 4. Programmatic source attribution: unique source files, in retrieval order.
    #    If the model refused (no grounded answer), don't list sources — they
    #    didn't contribute to the answer and would be misleading.
    REFUSAL = "I don't have enough information on that."
    if REFUSAL.lower() in answer.lower():
        return {"answer": answer, "sources": []}

    sources = []
    for doc, meta, dist in results:
        if meta["source"] not in sources:
            sources.append(meta["source"])

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Which CS 31 professor do students recommend?"
    result = ask(q)
    print(f"Q: {q}\n")
    print(f"A: {result['answer']}\n")
    print("Sources:")
    for s in result["sources"]:
        print(f"  • {s}")
