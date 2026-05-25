import json
from graph.state import CVState
from tools.cv_formatter import format_cv
from config.settings import llm_invoke


def report_generator_node(state: CVState) -> CVState:
    """Node 5 — Consolida score, gaps, CV revisado e recomendações no relatório final."""
    score = state["score"]
    gaps = state["gaps"]
    role = state["job_requirements"].get("role_title", "target role")
    matched = state["job_requirements"].get("keywords", [])

    prompt = f"""Generate a professional CV analysis report in Markdown.

Structure:
## Resultado da Análise
- **Score:** {score}/100 para {role}
- **Status:** [Forte match / Precisa de ajustes / Requer reformulação]

## Pontos Fortes
[list matched strengths based on the CV and keywords]

## Gaps Identificados
[list the gaps]

## Recomendações ATS
[list specific keywords to add and formatting tips]

## Próximos Passos
[3 concrete actions the candidate should take]

Use the data below. Be direct and actionable.

Gaps: {json.dumps(gaps, ensure_ascii=False)}
Matched keywords: {json.dumps(matched, ensure_ascii=False)}
Iterations used: {state.get('iterations', 0)}
"""
    report = llm_invoke(prompt).content

    # Se o CV ainda não foi formatado (veio do quick_feedback, já está pronto)
    revised = state.get("revised_cv", "")
    if not revised:
        revised = format_cv.invoke({"cv_data": state["parsed_cv"]})

    return {**state, "revised_cv": revised, "final_report": report}
