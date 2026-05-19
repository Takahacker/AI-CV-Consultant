import json
from langchain_core.tools import tool
from config.settings import llm


@tool
def extract_job_requirements(job_description: str) -> dict:
    """Extract structured requirements from a job description.
    Returns: {keywords[], must_have[], nice_to_have[], seniority, role_title}
    """
    prompt = f"""Extract the job requirements from the description below into a JSON object with exactly these keys:
- role_title (string)
- seniority (string: "junior", "mid", "senior", or "not specified")
- keywords (list of strings: important technical terms and tools)
- must_have (list of strings: non-negotiable requirements)
- nice_to_have (list of strings: preferred but optional requirements)

Return ONLY the JSON object, no explanation.

JOB DESCRIPTION:
{job_description}
"""
    response = llm.invoke(prompt)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"role_title": "", "seniority": "not specified", "keywords": [], "must_have": [], "nice_to_have": []}
