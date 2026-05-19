import json
from langchain_core.tools import tool
from config.settings import llm


@tool
def parse_cv(raw_text: str) -> dict:
    """Parse raw CV text into a structured dict.
    Returns: {name, email, summary, experience[], skills[], education[]}
    Each experience item: {title, company, period, bullets[]}
    Each education item: {degree, institution, period}
    """
    prompt = f"""Extract the CV information below into a JSON object with exactly these keys:
- name (string)
- email (string, empty string if not found)
- summary (string, professional summary or objective)
- experience (list of objects with: title, company, period, bullets)
- skills (list of strings)
- education (list of objects with: degree, institution, period)

Return ONLY the JSON object, no explanation.

CV TEXT:
{raw_text}
"""
    response = llm.invoke(prompt)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback: tentar extrair JSON do texto
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"name": "", "email": "", "summary": raw_text, "experience": [], "skills": [], "education": []}
