"""
inspect_chunks.py

Milestone 3 verification: print the chunks and check they meet our spec.

This script reuses the chunking pipeline from chunk_documents.py and then:
  1. Prints every chunk (so we can eyeball them for standalone meaning).
  2. Runs automated checks (assertions) from planning.md's verification plan:
       - every chunk has exactly one "Professor:" line
       - every chunk carries its source header (Source URL / Course)
       - every chunk is within the size cap (with a small tolerance)
       - no HTML tags or entities leaked into any chunk

Run:  python3 inspect_chunks.py
"""

import re

from chunk_documents import MAX_CHARS, load_documents, chunk_all

# Allow a tiny overshoot above MAX_CHARS: sentence-boundary splitting can land a
# few characters past the cap rather than cut a sentence in half. 1100 is a
# generous ceiling that still flags any genuinely oversized chunk.
SIZE_TOLERANCE = 1100


def print_chunks(chunks: list[dict]) -> None:
    """Print every chunk with its index, size, and source filename."""
    print(f"===== ALL {len(chunks)} CHUNKS =====")
    for i, c in enumerate(chunks):
        print(f"\n--- chunk {i} ({len(c['text'])} chars, {c['filename']}) ---")
        print(c["text"])


def verify_chunks(chunks: list[dict]) -> None:
    """Run automated checks on the chunks and report pass/fail per check."""
    print("\n===== VERIFICATION =====")

    problems = []

    for i, c in enumerate(chunks):
        text = c["text"]

        # Check 1: exactly one "Professor:" line — one review subject per chunk.
        prof_count = text.count("Professor:")
        if prof_count != 1:
            problems.append(f"chunk {i}: expected 1 'Professor:' line, found {prof_count}")

        # Check 2: source attribution header is present.
        if "Source URL:" not in text:
            problems.append(f"chunk {i}: missing 'Source URL:' header")

        # Check 3: within the size cap (with a small tolerance for sentence splits).
        if len(text) > SIZE_TOLERANCE:
            problems.append(f"chunk {i}: {len(text)} chars exceeds tolerance {SIZE_TOLERANCE}")

        # Check 4: no leftover HTML tags or entities.
        if re.search(r"<[a-zA-Z/][^>]*>", text):
            problems.append(f"chunk {i}: contains an HTML tag")
        if re.search(r"&[a-zA-Z]+;|&#\d+;", text):
            problems.append(f"chunk {i}: contains an HTML entity")

    # Report results.
    sizes = [len(c["text"]) for c in chunks]
    print(f"Total chunks: {len(chunks)}")
    print(f"Sizes — min {min(sizes)}, median {sorted(sizes)[len(sizes)//2]}, max {max(sizes)}")
    print(f"Chunks over {MAX_CHARS} chars: {sum(1 for s in sizes if s > MAX_CHARS)}")

    if problems:
        print(f"\nFAILED — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("\nPASSED — every chunk has one Professor line, a source header, "
              "is within the size cap, and contains no HTML artifacts.")


if __name__ == "__main__":
    docs = load_documents()
    chunks = chunk_all(docs)

    print_chunks(chunks)
    verify_chunks(chunks)
