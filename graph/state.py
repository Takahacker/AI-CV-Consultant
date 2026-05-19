from typing import TypedDict, Optional


class CVState(TypedDict):
    mode: str                        # "build" | "evaluate"
    raw_input: str                   # CV bruto (texto/PDF) ou dump livre de texto
    job_description: str             # Descrição da vaga colada pelo usuário
    parsed_cv: dict                  # {name, email, summary, experience[], skills[], education[]}
    job_requirements: dict           # {keywords[], must_have[], nice_to_have[], seniority}
    score: int                       # 0–100 calculado pelo gap_analyzer
    gaps: list                       # Lista de gaps identificados
    revised_cv: str                  # CV reescrito em Markdown
    iterations: int                  # Contador de iterações do DeepAgent
    final_report: str                # Output final exibido ao usuário
