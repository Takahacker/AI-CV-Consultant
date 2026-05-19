import json
from langchain_core.tools import tool
from config.settings import llm


@tool
def format_cv(cv_data: dict) -> str:
    """Format a structured CV dict into clean Markdown ready to copy/paste.
    Accepts either a structured dict or a raw string CV.
    """
    if isinstance(cv_data, str):
        return cv_data  # já está em Markdown

    prompt = f"""Convert the structured CV below into a clean, professional Markdown document.

Format it as:
# [Name]
[email]

## Resumo
[summary]

## Experiência
### [title] — [company] | [period]
- [bullet]
- [bullet]

## Habilidades
[skills as comma-separated or grouped list]

## Formação
### [degree] — [institution] | [period]

Return ONLY the Markdown, no explanation.

CV DATA:
{json.dumps(cv_data, ensure_ascii=False, indent=2)}
"""
    response = llm.invoke(prompt)
    return response.content
