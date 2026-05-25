import json
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from graph.state import CVState
from tools.cv_scorer import score_cv
from tools.cv_formatter import format_cv
from config.settings import llm, MAX_ITERATIONS, SCORE_THRESHOLD

_tavily_raw = TavilySearch(max_results=5)


@tool
def web_search(query: str) -> str:
    """Search the web for current information about a topic.

    Use to research ATS keywords, CV best practices for a specific role, and
    current job-market expectations. Accepts a plain text query only.

    Args:
        query: The search query string (e.g., "ATS keywords data scientist 2025").

    Returns:
        A formatted string with up to 5 results (title, URL, snippet).
    """
    try:
        result = _tavily_raw.invoke({"query": query})
    except Exception as e:
        return f"Search failed: {e}"
    items = result.get("results", []) if isinstance(result, dict) else []
    if not items:
        return "No results found."
    lines = []
    for r in items[:5]:
        title = r.get("title", "") or ""
        url = r.get("url", "") or ""
        content = (r.get("content", "") or "")[:300]
        lines.append(f"- {title}\n  {url}\n  {content}")
    return "\n".join(lines)


_agent = create_deep_agent(
    model=llm,
    tools=[web_search, score_cv, format_cv],
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
