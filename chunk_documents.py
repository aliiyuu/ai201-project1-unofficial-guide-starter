"""
chunk_documents.py

Milestone 3: load the raw scraped documents and split them into chunks.

We build this up one step at a time:
  Step 1 (this version): just LOAD the raw .txt files and report what we found.
  Step 2 (next): split each loaded document into one-review-per-chunk pieces.
"""

import re
from pathlib import Path

# Folder where build_documents.py wrote the raw scraped text files.
RAW_DIR = Path("documents/raw")

# Size limits from planning.md's Chunking Strategy.
MAX_CHARS = 1000      # hard cap: reviews longer than this get split
OVERLAP_CHARS = 100   # overlap carried between sub-chunks of one long review



def load_documents(raw_dir: Path = RAW_DIR) -> list[dict]:
    """Read every .txt file in raw_dir into memory.

    Returns a list of dicts, one per file, like:
        {"filename": "bruinwalk_cs31_reviews.txt", "text": "<full file text>"}

    Keeping the filename with the text matters: later we use it to remember
    which course/professor a chunk came from (source attribution).
    """
    documents = []
    for path in sorted(raw_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        documents.append({"filename": path.name, "text": text})
    return documents


def split_header_and_body(text: str) -> tuple[str, str]:
    """Separate the top header lines from the review body.

    Our raw files start with a few header lines (Source URL:, Course:) followed
    by a blank line, then the review blocks. We return (header, body) so we can
    later attach the header to every chunk for source attribution.
    """
    # The first blank line separates the header block from the body.
    parts = text.split("\n\n", 1)
    if len(parts) == 2:
        header, body = parts
    else:
        header, body = "", text
    return header.strip(), body.strip()


def chunk_document(doc: dict) -> list[dict]:
    """Split ONE loaded document into review-block chunks.

    Steps:
      1. Separate header (Source URL / Course) from the body.
      2. Split the body on the '---' delimiter into review blocks.
      3. Skip blocks that have no actual review (blank lines or the
         '=== professor url ===' separators with no content).
      4. Prepend the header to each kept block so the chunk is self-describing.

    Returns a list of dicts: {"filename", "text"} — one per chunk.
    """
    header, body = split_header_and_body(doc["text"])

    chunks = []
    for block in body.split("---"):
        block = block.strip()

        # Skip empty pieces and the "=== .../professors/... ===" separator lines
        # that appear with no review text under them. A real review block always
        # has an "Overall Rating:" line (the labelled subject is "Professor:" on
        # class pages or "Course:" on professor pages, so we can't key on that).
        if not block or "Overall Rating:" not in block:
            continue

        # Glue the header on so the chunk keeps its course/source attribution.
        chunk_text = f"{header}\n\n{block}" if header else block
        chunks.append({"filename": doc["filename"], "text": chunk_text})

    return chunks


def split_oversized_chunk(chunk: dict) -> list[dict]:
    """Split a chunk that exceeds MAX_CHARS into smaller, overlapping pieces.

    A few reviews (e.g. Reinman's CS 33 essay) are very long. We keep the
    attribution prefix (header + Professor/Rating lines, up to and including the
    'Most Helpful Review:' label) on every piece, then split the long review
    text on sentence boundaries, packing sentences into ~MAX_CHARS windows with
    ~OVERLAP_CHARS of overlap so a thought split across a boundary isn't lost.
    """
    text = chunk["text"]
    if len(text) <= MAX_CHARS:
        return [chunk]  # already small enough, leave it alone

    # 1. Separate the attribution prefix from the long review body.
    #    Everything up to "Most Helpful Review:" identifies who/what this is.
    marker = "Most Helpful Review:"
    if marker in text:
        prefix, body = text.split(marker, 1)
        prefix = prefix.strip()  # header + Professor/Rating lines only
    else:
        prefix, body = "", text

    # 2. Split the review body into sentences (after . ! ? followed by space).
    sentences = re.split(r"(?<=[.!?])\s+", body.strip())

    # 3. Greedily pack sentences into windows under MAX_CHARS, with overlap.
    pieces = []
    current = ""
    for sentence in sentences:
        if current and len(prefix) + len(current) + len(sentence) > MAX_CHARS:
            pieces.append(current.strip())
            # Carry the tail of the previous window forward as overlap, but
            # start it at a word boundary so we never cut a word in half.
            tail = current[-OVERLAP_CHARS:]
            tail = tail[tail.find(" ") + 1:] if " " in tail else tail
            current = tail + " " + sentence
        else:
            current = (current + " " + sentence).strip()
    if current.strip():
        pieces.append(current.strip())

    # 4. Re-attach the prefix to every piece so each stays self-describing.
    #    The first piece keeps the "Most Helpful Review:" label; continuation
    #    pieces are marked "(cont.)" so it's clear they're mid-review.
    result = []
    for i, piece in enumerate(pieces):
        label = "Most Helpful Review:" if i == 0 else "Review (cont.):"
        result.append({
            "filename": chunk["filename"],
            "text": f"{prefix}\n{label} {piece}".strip(),
        })
    return result



def chunk_all(documents: list[dict]) -> list[dict]:
    """Run the full chunking pipeline over all loaded documents.

    Splits each document into review blocks, then enforces the size cap on any
    oversized block. Returns the final flat list of chunk dicts.
    """
    all_chunks = []
    for doc in documents:
        for chunk in chunk_document(doc):
            all_chunks.extend(split_oversized_chunk(chunk))
    return all_chunks


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from {RAW_DIR}/\n")

    all_chunks = chunk_all(docs)

    sizes = [len(c["text"]) for c in all_chunks]
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Sizes — min {min(sizes)}, median {sorted(sizes)[len(sizes)//2]}, max {max(sizes)}")
    print(f"Chunks over {MAX_CHARS} chars: {sum(1 for s in sizes if s > MAX_CHARS)}")

    # Print 5 representative chunks to inspect (per the assignment).
    print("\n===== 5 REPRESENTATIVE CHUNKS =====")
    for i in (0, 5, 10, 15, 20):
        if i < len(all_chunks):
            c = all_chunks[i]
            print(f"\n--- chunk {i} ({len(c['text'])} chars, {c['filename']}) ---")
            print(c["text"])


