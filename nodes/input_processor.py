import json
from graph.state import CVState
from tools.cv_parser import parse_cv
from config.settings import llm


def input_processor_node(state: CVState) -> CVState:
    """Node 1 — Parseia CV existente (modo evaluate) ou extrai info de dump livre (modo build)."""
    raw = state["raw_input"]

    if state["mode"] == "evaluate":
        parsed = parse_cv.invoke({"raw_text": raw})
    else:
        # Modo build: dump livre → LLM extrai e organiza como se fosse um CV
        prompt = f"""The user provided a free-form text with their professional background.
Extract and organize it exactly as a structured CV JSON with keys:
name, email, summary, experience (list of {{title, company, period, bullets}}),
skills (list of strings), education (list of {{degree, institution, period}}).

Infer and fill gaps where possible. If a field is missing, use an empty string or empty list.
Return ONLY the JSON object.

TEXT:
{raw}
"""
        response = llm.invoke(prompt)
        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            parsed = json.loads(match.group()) if match else {}

    return {**state, "parsed_cv": parsed}
