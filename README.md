# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Demo

A screen recording of the Gradio interface answering grounded questions and refusing an out-of-corpus question: [demo.mp4](demo.mp4)

> On GitHub the link opens an inline video player. To run it locally: `source .venv/bin/activate && python app.py`, then open http://localhost:7860.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Student reviews of UCLA Computer Science courses and professors. Official sources (the registrar catalog, syllabi) only describe *what* a course covers. They say nothing about a professor's teaching style, exam difficulty, grading strictness, or weekly workload. That experiential knowledge lives only in student forums and review sites, where people who actually took the class describe what it was really like. This RAG system makes this knowledge queryable by students.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Bruinwalk — CS 31 reviews | Course review page | https://www.bruinwalk.com/classes/com-sci-31/ → documents/raw/bruinwalk_cs31_reviews.txt |
| 2 | Bruinwalk — CS 32 reviews | Course review page | https://www.bruinwalk.com/classes/com-sci-32/ → documents/raw/bruinwalk_cs32_reviews.txt |
| 3 | Bruinwalk — CS 33 reviews | Course review page | https://www.bruinwalk.com/classes/com-sci-33/ → documents/raw/bruinwalk_cs33_reviews.txt |
| 4 | Bruinwalk — CS 35L reviews | Course review page | https://www.bruinwalk.com/classes/com-sci-35l/ → documents/raw/bruinwalk_cs35l_reviews.txt |
| 5 | Bruinwalk — Prof. Yutao He | Professor review page | https://www.bruinwalk.com/professors/yutao-he/ → documents/raw/bruinwalk_prof_yutao_he.txt |
| 6 | Bruinwalk — Prof. Bruce Huang | Professor review page | https://www.bruinwalk.com/professors/bruce-huang/ → documents/raw/bruinwalk_prof_bruce_huang.txt |
| 7 | Bruinwalk — Prof. Ani Nahapetian | Professor review page | https://www.bruinwalk.com/professors/ani-nahapetian/ → documents/raw/bruinwalk_prof_ani_nahapetian.txt |
| 8 | Bruinwalk — Prof. John A. Rohr | Professor review page | https://www.bruinwalk.com/professors/john-a-rohr/ → documents/raw/bruinwalk_prof_john_a_rohr.txt |
| 9 | Bruinwalk — Prof. Edwin Ambrosio | Professor review page | https://www.bruinwalk.com/professors/edwin-ambrosio/ → documents/raw/bruinwalk_prof_edwin_ambrosio.txt |
| 10 | Bruinwalk — Prof. Carey Nachenberg | Professor review page | https://www.bruinwalk.com/professors/carey-nachenberg/ → documents/raw/bruinwalk_prof_carey_nachenberg.txt |

> Reddit r/ucla, the UCLA registrar catalog, and the grades.natecation explorer were dropped during implementation: Reddit returns HTTP 403 to unauthenticated scrapers, and the other two are JS-rendered (a plain `requests` scrape only captured title stubs / "Loading..." placeholders). They were replaced with individual Bruinwalk professor pages for professors who teach the popular intro CS series.

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** One review block per chunk (target ~500 characters, hard cap ~1000). Each raw document is already a series of self-contained review blocks separated by a `\n---\n` delimiter, so the chunker splits on that boundary rather than on a fixed window.

**Overlap:** None between different review blocks. A sentence-boundary split with ~100-character (word-aligned) overlap is applied only as a fallback to the handful of oversized reviews that exceed the 1000-char cap.

**Why these choices fit:** The corpus is review-heavy. Every block is one professor's structured rating line (Easiness/Clarity/Workload/Helpfulness) plus a "Most Helpful Review" comment. A fixed-size sliding window would slice mid-review, merging completely unrelated professors into a single embedding. Splitting on the `---` boundary keeps each professor's review independently retrievable. Each document's `Source URL` / `Course` header is prepended to every chunk so a retrieved review keeps its course/professor attribution.

**Preprocessing:** The scraper (`build_documents.py`) extracts clean structured fields (professor, course, ratings, review text) directly from Bruinwalk's HTML, so no HTML tags, entities, or nav boilerplate ever reach the chunks (verified zero artifacts via `inspect_chunks.py`). This part is taken care of before chunking, so it doesn't need to be done as part of the chunking process.

**Final chunk count:** 41 chunks across 11 documents (min 260 / median 634 / max 1022 characters).

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers (384-dimensional embeddings). It is free, runs locally with no API key, and is well-suited to the short, English, review-length text in this corpus. Retrieval uses top-k = 5, stored in a local Chroma vector database.

**Production tradeoff reflection:** If cost weren't a constraint and this served real users, I'd consider a stronger model such as OpenAI `text-embedding-3-large` or a top MTEB model such as `bge-large-en-v1.5`. Larger models capture subtler sentiment and paraphrase, which improves recall on differently-worded queries. A longer context window would matter only if I switched to whole-professor-page chunks, and a multilingual model would matter if the corpus expanded beyond English (one review here is in Chinese). Given the small and mainly English corpus, MiniLM is the right default.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt instruction:** The system prompt (in `query.py`) enforces grounding. It instructs the model to "Answer using ONLY the information in the provided context. Do not use any outside or prior knowledge," to reply with exactly `"I don't have enough information on that."` when the context is insufficient, and to never invent professors, ratings, or quotes. The user turn formats the retrieved chunks into a labeled context block followed by the question, and generation runs at `temperature=0` to ensure the model follows that context.

**How source attribution is surfaced in the response:** Sources are attached programmatically, not by the LLM. After generation, `ask()` collects the unique `source` filenames from the retrieved chunks' Chroma metadata (in retrieval order) and returns them with the answer. This guarantees that source attribution can't be hallucinated or left out. When the model refuses (out-of-corpus question), the source list gets suppressed since no chunk contributed to the answer.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which CS 31 professor do students most recommend, and why? | Bruce Huang — nice with grades, passionate, gives extra credit; one reviewer recommends him over any other CS 31 professor. | Named Bruce Huang and quoted "would definitely recommend taking CS31 with him over any other professor." | Relevant (rank 1) | Accurate |
| 2 | How do students describe Howard Stahl's CS 32 difficulty/grading vs Smallberg/Nachenberg? | Easier than Smallberg/Nachenberg; easy projects, fair exams, lenient regrades, an A is doable. | "Definitely easier than CS32 with Smallberg/Nachenberg," projects "almost too easy," exams "fair," lenient regrades, "100% doable." | Relevant (rank 1) | Accurate |
| 3 | What do reviews say about Paul Eggert's CS 33 class? | Very negative on difficulty; "Leave now!! Wrote with blood and tear"; low easiness/workload. | Quoted "Leave now!!" warning and reported the 1.4/5 easiness, 1.7/5 workload ratings. | Relevant (Eggert at rank 4, still retrieved) | Accurate |
| 4 | What are students' main complaints about Glenn Reinman's CS 33 course? | Content-heavy flipped videos, brutal 40-min midterm (avg 49), academic-integrity obsession, harsh curve. | Listed content-heavy videos, the six-version 40-min midterm, "nonsensical" grading (only 35% A-range), mandatory discussions. | Relevant (rank 1, 4 of 5 chunks Reinman) | Accurate |
| 5 | How do students feel about David Smallberg despite his lecture style? | Boring lectures (no slides, codes in Word) but "an absolute legend and a wonderful man." | "an absolute legend and a wonderful man" despite boring lectures / coding in Word. | Relevant (rank 1) | Accurate |

**Retrieval quality:** Very relevant (5/5 questions retrieved the expected professor within top-5; Q3 placed Eggert at rank 4 because the open-ended phrasing also pulled other CS 33 professors)
**Response accuracy:** Accurate (all 5 grounded in real review text with correct programmatic source attribution)

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "What do reviews say about Paul Eggert's CS 33 class?" (Q3), a partial retrieval weakness rather than an outright failure.

**What the system returned:** A correct, accurate answer about Eggert, but only because the top-5 included his chunk at rank 4. Ranks 1–3 were other CS 33 professors (Ghaforyfard, Nowatzki, Smallberg).

**Root cause (tied to a specific pipeline stage):** This is an embedding/retrieval-stage issue. Eggert's review is short and its strongest signal ("Leave now!! Wrote with blood and tear") is emotional rather than topical, so its embedding is less similar to the literal query terms ("reviews," "CS 33," "class") than longer, more descriptive CS 33 reviews. The query embeds toward generic "CS 33 course review" content, so verbose reviews from other professors rank higher than the specifically relevant short one.

**What I would change to fix it:** Add some lightweight metadata filtering. Parse the professor name from the query and pre-filter the Chroma query by a `professor` metadata field so only matching chunks compete. Alternatively, increase top-k or use a stronger embedding model. For this corpus the simplest robust fix is metadata-aware retrieval when a professor is named.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped during implementation:** Writing the Chunking Strategy in `planning.md` before coding forced the decision to split on the natural `---` review boundary instead of a fixed-size window. When I later implemented `chunk_documents.py`, that plan quickly and directly dictated the structure-aware splitter and the rule to prepend each document's header for attribution.

**One way your implementation diverged from the spec, and why:** The plan listed Reddit r/ucla, the UCLA catalog, and a grade-distribution site as sources. During implementation all three proved unscrapable (Reddit 403s unauthenticated requests; the others are JS-rendered and returned only placeholders). I diverged by replacing them with individual Bruinwalk professor pages for professors teaching the popular intro CS series, which kept the source count and the "different perspectives" goal intact while using pages that actually render on the server-side.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* My Chunking Strategy section from `planning.md` and a sample raw review file, asking it to implement the chunker.
- *What it produced:* `chunk_documents.py` splitting on the `---` delimiter, prepending the header, and a `split_oversized_chunk()` fallback for long reviews.
- *What I changed or overrode:* The first overlap implementation cut mid-word ("once again" => "ce again"); I directed it to align the overlap to a word boundary. I also changed the block-skip check from keying on `Professor:` to `Overall Rating:` after discovering professor-page cards use a different label.

**Instance 2**

- *What I gave the AI:* My Retrieval Approach and the grounding requirement, asking it to wire up generation + a Gradio UI that answers from retrieved context only with source attribution.
- *What it produced:* `query.py` (strict system prompt, Groq `llama-3.3-70b-versatile`, programmatic source attribution) and `app.py` (Gradio).
- *What I changed or overrode:* I had it suppress the source list on refusal answers (listing sources for an "I don't have enough information" reply is misleading) and set `temperature=0` to keep generation anchored to the retrieved context.
