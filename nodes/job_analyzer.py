from graph.state import CVState
from tools.job_extractor import extract_job_requirements


def job_analyzer_node(state: CVState) -> CVState:
    """Node 2 — Extrai requisitos estruturados da descrição da vaga."""
    requirements = extract_job_requirements.invoke({"job_description": state["job_description"]})
    return {**state, "job_requirements": requirements}
