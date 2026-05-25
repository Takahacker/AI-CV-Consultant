import json
from langchain_core.tools import tool
from config.settings import llm_invoke


@tool
def score_cv(parsed_cv: dict, job_requirements: dict) -> dict:
    """Compare a structured CV against job requirements.
    Returns: {score (0-100), gaps[], matched_keywords[], suggestions[]}
    """
    prompt = f"""You are an ATS (Applicant Tracking System) evaluator.

Compare the CV below against the job requirements and return a JSON object with:
- score (integer 0-100): overall match percentage
- matched_keywords (list of strings): keywords from the job found in the CV
- gaps (list of strings): important requirements missing from the CV
- suggestions (list of strings): specific actionable improvements

Be strict: a score of 80+ means the CV is genuinely strong for this role.

Return ONLY the JSON object, no explanation.

CV:
{json.dumps(parsed_cv, ensure_ascii=False, indent=2)}

JOB REQUIREMENTS:
{json.dumps(job_requirements, ensure_ascii=False, indent=2)}
"""
    response = llm_invoke(prompt)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"score": 0, "matched_keywords": [], "gaps": [], "suggestions": []}
