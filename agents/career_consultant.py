import json
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_tavily import TavilySearch

from graph.state import CVState
from tools.cv_scorer import score_cv
from tools.cv_formatter import format_cv
from config.settings import llm, MAX_ITERATIONS, SCORE_THRESHOLD

_tavily = TavilySearch(max_results=5)

_agent = create_deep_agent(
    model=llm,
    tools=[_tavily, score_cv, format_cv],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    skills=["/skills/"],
    system_prompt=(
        "You are a senior career consultant and CV specialist. "
        "Use the cv-rewriter skill to research current market standards and rewrite the CV. "
        "Use score_cv to evaluate the result after each rewrite iteration. "
        f"Stop when the score reaches {SCORE_THRESHOLD} or after {MAX_ITERATIONS} iterations. "
        "Use format_cv to produce the final clean Markdown CV. "
        "Return your final answer as a JSON object with keys: "
        "revised_cv (string), score (int), iterations (int), changes_summary (string)."
    ),
)


def career_consultant_node(state: CVState) -> CVState:
    """Node 4b — DeepAgent que pesquisa o mercado e reescreve o CV iterativamente."""
    prompt = f"""Rewrite the CV below to better match the job requirements.

Current score: {state['score']}/100
Target score: {SCORE_THRESHOLD}
Max iterations: {MAX_ITERATIONS}

CV (structured):
{json.dumps(state['parsed_cv'], ensure_ascii=False, indent=2)}

Job Requirements:
{json.dumps(state['job_requirements'], ensure_ascii=False, indent=2)}

Gaps to address:
{json.dumps(state['gaps'], ensure_ascii=False, indent=2)}

Use the cv-rewriter skill. Research the market first, then rewrite and score iteratively.
"""
    result = _agent.invoke({"messages": [{"role": "user", "content": prompt}]})

    # Extrair a última mensagem do agente
    last_msg = result["messages"][-1].content

    try:
        import re
        match = re.search(r'\{.*\}', last_msg, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    except (json.JSONDecodeError, AttributeError):
        data = {}

    return {
        **state,
        "revised_cv": data.get("revised_cv", last_msg),
        "score": data.get("score", state["score"]),
        "iterations": data.get("iterations", MAX_ITERATIONS),
    }
