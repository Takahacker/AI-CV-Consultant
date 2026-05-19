from langgraph.graph import StateGraph, END

from graph.state import CVState
from nodes.input_processor import input_processor_node
from nodes.job_analyzer import job_analyzer_node
from nodes.gap_analyzer import gap_analyzer_node
from nodes.quick_feedback import quick_feedback_node
from nodes.report_generator import report_generator_node
from agents.career_consultant import career_consultant_node
from config.settings import SCORE_THRESHOLD


def _route_by_score(state: CVState) -> str:
    if state["score"] >= SCORE_THRESHOLD:
        return "quick_feedback"
    return "career_consultant"


def build_graph():
    graph = StateGraph(CVState)

    graph.add_node("input_processor",   input_processor_node)
    graph.add_node("job_analyzer",      job_analyzer_node)
    graph.add_node("gap_analyzer",      gap_analyzer_node)
    graph.add_node("quick_feedback",    quick_feedback_node)
    graph.add_node("career_consultant", career_consultant_node)
    graph.add_node("report_generator",  report_generator_node)

    graph.set_entry_point("input_processor")
    graph.add_edge("input_processor", "job_analyzer")
    graph.add_edge("job_analyzer",    "gap_analyzer")

    graph.add_conditional_edges(
        "gap_analyzer",
        _route_by_score,
        {
            "quick_feedback":    "quick_feedback",
            "career_consultant": "career_consultant",
        },
    )

    graph.add_edge("quick_feedback",    "report_generator")
    graph.add_edge("career_consultant", "report_generator")
    graph.add_edge("report_generator",  END)

    return graph.compile()


# Instância global para importar em app.py
cv_graph = build_graph()
