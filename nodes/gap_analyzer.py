from graph.state import CVState
from tools.cv_scorer import score_cv


def gap_analyzer_node(state: CVState) -> CVState:
    """Node 3 — Calcula score 0-100 e identifica gaps entre CV e vaga."""
    result = score_cv.invoke({
        "parsed_cv": state["parsed_cv"],
        "job_requirements": state["job_requirements"],
    })
    return {
        **state,
        "score": result.get("score", 0),
        "gaps": result.get("gaps", []),
    }
