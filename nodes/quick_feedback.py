import json
from graph.state import CVState
from tools.cv_formatter import format_cv
from config.settings import llm


def quick_feedback_node(state: CVState) -> CVState:
    """Node 4a — Caminho rápido quando score >= 80. Gera sugestões leves sem reescrever o CV."""
    prompt = f"""The candidate's CV scores {state['score']}/100 for this role. It is a strong match.

Write a short, encouraging feedback (3-5 bullet points) highlighting:
- What is already strong in the CV
- 2-3 minor improvements to make it even better

Be specific and actionable. Use the gaps below as reference.

Gaps identified: {json.dumps(state['gaps'], ensure_ascii=False)}
Role: {state['job_requirements'].get('role_title', 'the target role')}
"""
    feedback = llm.invoke(prompt).content
    formatted = format_cv.invoke({"cv_data": state["parsed_cv"]})

    return {**state, "revised_cv": formatted, "final_report": feedback}
