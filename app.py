"""
app.py

Milestone 5 interface: a minimal Gradio web UI over the grounded RAG pipeline.

The UI is intentionally thin — all the real logic (retrieval, grounding prompt,
generation, source attribution) lives in query.ask(). This file just wires a
text box to that function and shows the answer plus the sources it was grounded in.

Run:  python app.py     then open http://localhost:7860
"""

import gradio as gr

from query import ask


def handle_query(question: str):
    """Run one question through the RAG pipeline and format it for the UI."""
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — UCLA CS Reviews") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about UCLA CS courses and professors. Answers come **only** from "
        "scraped Bruinwalk student reviews — if the reviews don't cover it, the "
        "system says so instead of guessing."
    )

    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. Which CS 31 professor do students recommend?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
