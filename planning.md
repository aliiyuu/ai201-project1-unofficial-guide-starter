# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
Course and professor reviews would be a strong domain. Typically, the only information available about most university courses from official sources consists of course descriptions and syllabi. There is little to no info on the individual teaching styles of each professor and how accessible each individual course offering is. These insights are usually only found on student forums, where students who actually have taken certain classes discuss their experiences.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Bruinwalk - CS 31 reviews snapshot | Extracted review text for workload, pace, and exam style (source: https://www.bruinwalk.com/classes/com-sci-31/) | documents/raw/bruinwalk_cs31_reviews.txt |
| 2 | Bruinwalk - CS 32 reviews snapshot | Extracted review text for CS 32 difficulty jump and project load (source: https://www.bruinwalk.com/classes/com-sci-32/) | documents/raw/bruinwalk_cs32_reviews.txt |
| 3 | Bruinwalk - CS 33 reviews snapshot | Extracted review text for lab intensity, quizzes, and grading strictness (source: https://www.bruinwalk.com/classes/com-sci-33/) | documents/raw/bruinwalk_cs33_reviews.txt |
| 4 | Bruinwalk - CS 35L reviews snapshot | Extracted review text for tooling friction and weekly time commitment (source: https://www.bruinwalk.com/classes/com-sci-35l/) | documents/raw/bruinwalk_cs35l_reviews.txt |
| 5 | Bruinwalk - professor reviews snapshot | Aggregated professor-specific comments for clarity, accessibility, and teaching style (source: Bruinwalk professor pages) | documents/raw/bruinwalk_professor_reviews.txt |
| 6 | Bruinwalk - CS professor 1 | Individual review page for a professor teaching a popular CS course | documents/raw/bruinwalk_prof_yutao_he.txt |
| 7 | Bruinwalk - CS professor 2 | Individual review page for a professor teaching a popular CS course | documents/raw/bruinwalk_prof_bruce_huang.txt |
| 8 | Bruinwalk - CS professor 3 | Individual review page for a professor teaching a popular CS course | documents/raw/bruinwalk_prof_ani_nahapetian.txt |
| 9 | Bruinwalk - CS professor 4 | Individual review page for a professor teaching a popular CS course | documents/raw/bruinwalk_prof_john_a_rohr.txt |
| 10 | Bruinwalk - CS professor 5 | Individual review page for a professor teaching a popular CS course | documents/raw/bruinwalk_prof_edwin_ambrosio.txt |
| 11 | Bruinwalk - CS professor 6 | Individual review page for a professor teaching a popular CS course | documents/raw/bruinwalk_prof_carey_nachenberg.txt |

> Note: Reddit r/ucla sources were dropped — Reddit now returns HTTP 403 to
> unauthenticated scrapers (even the `.json` API) and requires OAuth or a real
> browser session. The UCLA registrar catalog pages and the grades.natecation
> grade-distribution explorer were also dropped: both are JS-rendered, so a plain
> `requests` scrape only captured a title stub or a "Loading ..." placeholder.
> They were replaced with individual Bruinwalk review pages for professors who
> teach the most popular CS courses (the CS 31/32/33/35L intro series). Professors
> with no written reviews are skipped automatically.

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
