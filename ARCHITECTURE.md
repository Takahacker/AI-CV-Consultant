# AI CV Consultant — Architecture Guide

## Problema real
Candidatos submetem CVs genéricos que são rejeitados por ATS (Applicant Tracking Systems)
antes de chegar a um recrutador humano, sem saber o que falta ou como adaptar para cada vaga.

---

## Stack
| Componente | Tecnologia |
|---|---|
| Orquestração | LangGraph + LangChain |
| LLM | NVIDIA NIM via `langchain_nvidia_ai_endpoints.ChatNVIDIA` |
| Web search | Tavily via `langchain-tavily` |
| Interface | Streamlit |
| Rastreamento | LangSmith |
| DeepAgent | `deepagents.create_deep_agent` + `FilesystemBackend` |

---

## Estrutura de arquivos

```
AI-CV-Consultant/
│
├── app.py                        # Entry point Streamlit
├── .env                          # NVIDIA_API_KEY, TAVILY_API_KEY, LANGCHAIN_API_KEY
├── requirements.txt
│
├── graph/
│   ├── state.py                  # CVState TypedDict — estado compartilhado do grafo
│   └── workflow.py               # StateGraph: nodes, edges, router, compilação
│
├── nodes/
│   ├── input_processor.py        # Node 1 — parseia CV existente OU extrai info de dump
│   ├── job_analyzer.py           # Node 2 — extrai keywords e requisitos da vaga
│   ├── gap_analyzer.py           # Node 3 — score 0-100 + lista de gaps
│   ├── quick_feedback.py         # Node 4a — caminho rápido (score >= 80)
│   └── report_generator.py       # Node 5 — relatório final + CV revisado
│
├── agents/
│   └── career_consultant.py      # Node 4b — DeepAgent com loop de reescrita
│
├── skills/
│   └── cv-rewriter/
│       └── SKILL.md              # SKILL do DeepAgent (web search + reescrita)
│
├── tools/
│   ├── cv_parser.py              # @tool — parseia PDF ou texto bruto → dict estruturado
│   ├── job_extractor.py          # @tool — extrai keywords/requisitos da descrição
│   ├── cv_scorer.py              # @tool — retorna score int + lista de gaps
│   └── cv_formatter.py           # @tool — formata CV revisado em Markdown limpo
│
├── prompts/
│   ├── input_processor.txt
│   ├── job_analyzer.txt
│   ├── gap_analyzer.txt
│   ├── career_consultant.txt
│   └── report_generator.txt
│
└── config/
    └── settings.py               # init do LLM, constantes (SCORE_THRESHOLD, MAX_ITERATIONS)
```

---

## graph/state.py

Estado central passado entre todos os nodes.

```python
from typing import TypedDict, Optional

class CVState(TypedDict):
    mode: str                    # "build" | "evaluate"
    raw_input: str               # CV bruto (texto ou conteúdo PDF) ou dump livre
    job_description: str         # Descrição da vaga colada pelo usuário
    parsed_cv: dict              # CV estruturado: {name, experience[], skills[], education[]}
    job_requirements: dict       # {keywords: [], must_have: [], nice_to_have: []}
    score: int                   # 0–100, calculado pelo gap_analyzer
    gaps: list[str]              # Lista de gaps identificados
    revised_cv: str              # CV reescrito pelo DeepAgent (Markdown)
    iterations: int              # Contador de iterações do DeepAgent
    final_report: str            # Output final para o usuário
```

---

## graph/workflow.py

Esqueleto do grafo com nodes, router e conditional edge.

```python
from langgraph.graph import StateGraph, END
from graph.state import CVState
from nodes.input_processor import input_processor_node
from nodes.job_analyzer import job_analyzer_node
from nodes.gap_analyzer import gap_analyzer_node
from nodes.quick_feedback import quick_feedback_node
from nodes.report_generator import report_generator_node
from agents.career_consultant import career_consultant_node

SCORE_THRESHOLD = 80

def route_by_score(state: CVState) -> str:
    if state["score"] >= SCORE_THRESHOLD:
        return "quick_feedback"
    return "career_consultant"

def build_graph():
    graph = StateGraph(CVState)

    graph.add_node("input_processor",    input_processor_node)
    graph.add_node("job_analyzer",       job_analyzer_node)
    graph.add_node("gap_analyzer",       gap_analyzer_node)
    graph.add_node("quick_feedback",     quick_feedback_node)
    graph.add_node("career_consultant",  career_consultant_node)
    graph.add_node("report_generator",   report_generator_node)

    graph.set_entry_point("input_processor")
    graph.add_edge("input_processor", "job_analyzer")
    graph.add_edge("job_analyzer",    "gap_analyzer")

    # ROUTER — conditional edge baseado no score
    graph.add_conditional_edges(
        "gap_analyzer",
        route_by_score,
        {
            "quick_feedback":    "quick_feedback",
            "career_consultant": "career_consultant",
        }
    )

    graph.add_edge("quick_feedback",    "report_generator")
    graph.add_edge("career_consultant", "report_generator")
    graph.add_edge("report_generator",  END)

    return graph.compile()
```

---

## nodes/ — responsabilidade de cada node

### Node 1 — input_processor.py
- **Modo `evaluate`**: recebe texto/PDF do CV, chama `cv_parser` tool, popula `parsed_cv`
- **Modo `build`**: recebe dump livre de texto, usa LLM para extrair e estruturar experiências, skills e formação no mesmo formato de `parsed_cv`
- Output: `state["parsed_cv"]` preenchido

### Node 2 — job_analyzer.py
- Recebe `state["job_description"]`
- Chama `job_extractor` tool
- Output: `state["job_requirements"]` com `keywords`, `must_have`, `nice_to_have`

### Node 3 — gap_analyzer.py
- Compara `parsed_cv` vs `job_requirements`
- Chama `cv_scorer` tool → retorna score e lista de gaps
- Output: `state["score"]`, `state["gaps"]`

### Node 4a — quick_feedback.py
- Ativado quando `score >= 80`
- Gera feedback textual simples: "Seu CV está bem alinhado. Sugestões menores: ..."
- NÃO reescreve o CV
- Output: `state["revised_cv"]` = CV original com anotações leves

### Node 4b — career_consultant.py (DeepAgent)
- Ativado quando `score < 80`
- Ver seção DeepAgent abaixo
- Output: `state["revised_cv"]`, `state["score"]` atualizado, `state["iterations"]`

### Node 5 — report_generator.py
- Consolida tudo em `state["final_report"]`
- Chama `cv_formatter` tool para formatar o CV revisado
- Output: relatório com score, gaps, CV revisado, keywords ATS sugeridas

---

## agents/career_consultant.py — DeepAgent

Loop de reescrita iterativa com máximo de 3 iterações.

```python
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_tavily import TavilySearch
from tools.cv_scorer import score_cv
from tools.cv_formatter import format_cv
from config.settings import llm

MAX_ITERATIONS = 3
SCORE_THRESHOLD = 80

tavily_tool = TavilySearch(max_results=5)

career_agent = create_deep_agent(
    model=llm,
    tools=[tavily_tool, score_cv, format_cv],
    backend=FilesystemBackend(root_dir="."),
    skills=["skills/"],          # lê skills/cv-rewriter/SKILL.md
    system_prompt=(
        "You are a senior career consultant. "
        "Use the cv-rewriter skill to research market standards and rewrite CV sections. "
        "Use score_cv to evaluate the result after each rewrite. "
        "Stop when the score reaches 80 or after 3 iterations."
    ),
)

def career_consultant_node(state: CVState) -> CVState:
    prompt = (
        f"Rewrite the CV below to better match the job requirements.\n\n"
        f"CV:\n{state['parsed_cv']}\n\n"
        f"Job Requirements:\n{state['job_requirements']}\n\n"
        f"Current gaps: {state['gaps']}\n\n"
        f"Target score: {SCORE_THRESHOLD}. Max iterations: {MAX_ITERATIONS}."
    )
    result = career_agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    # extrair revised_cv e novo score do resultado
    ...
    return {**state, "revised_cv": revised_cv, "score": new_score, "iterations": iterations}
```

---

## skills/cv-rewriter/SKILL.md

```markdown
---
name: cv-rewriter
description: Use this skill when asked to rewrite a CV to better match a specific job description. Includes web research for market standards and iterative scoring.
---

# cv-rewriter

## Goal
Rewrite CV sections using results-oriented language aligned with the target job's keywords and market expectations.

## Workflow
1. Read the current CV, job requirements, and gap list from the task.
2. Use `TavilySearch` to search for:
   - "best CV format for [job title] [year]"
   - "keywords ATS [job title]"
   - "required skills [job title] market"
3. Rewrite the experience bullet points using action verbs and quantified results.
4. Add missing keywords naturally into skills and experience sections.
5. Call `score_cv` to evaluate the new version.
6. If score < 80 and iterations < 3, repeat from step 2 with the new version.
7. Return the final revised CV in Markdown format.

## Output format
- Revised CV in Markdown
- Final score
- Summary of changes made
```

---

## tools/ — assinatura de cada ferramenta

```python
# cv_parser.py
@tool
def parse_cv(raw_text: str) -> dict:
    """Parse raw CV text into structured dict with keys:
    name, email, summary, experience (list), skills (list), education (list)."""

# job_extractor.py
@tool
def extract_job_requirements(job_description: str) -> dict:
    """Extract structured requirements from job description.
    Returns: {keywords: [], must_have: [], nice_to_have: [], seniority: str}"""

# cv_scorer.py
@tool
def score_cv(parsed_cv: dict, job_requirements: dict) -> dict:
    """Compare CV against job requirements.
    Returns: {score: int (0-100), gaps: list[str], matched_keywords: list[str]}"""

# cv_formatter.py
@tool
def format_cv(cv_data: dict) -> str:
    """Format structured CV dict into clean Markdown ready to copy/paste."""
```

---

## config/settings.py

```python
import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",  # ou outro modelo NVIDIA NIM disponível
    api_key=os.environ["NVIDIA_API_KEY"],
    temperature=0,
)

SCORE_THRESHOLD = 80
MAX_ITERATIONS = 3
```

---

## app.py — Streamlit UI

Fluxo da interface:

```
1. Sidebar: modo (Tenho um CV / Construir do zero)
2. Se modo "evaluate":
   - Upload PDF  OU  text_area para colar CV
3. Se modo "build":
   - text_area grande para dump livre de informações
4. text_area para colar a descrição da vaga
5. Botão "Analisar"
6. Exibe: score gauge + gaps + CV revisado + relatório
```

---

## Ordem de implementação

```
[ ] 1. config/settings.py           — init do LLM, checar conexão NVIDIA API
[ ] 2. graph/state.py               — definir CVState
[ ] 3. tools/cv_scorer.py           — ferramenta mais crítica, testar isolada
[ ] 4. tools/cv_parser.py + job_extractor.py
[ ] 5. nodes/input_processor.py     — testar modo evaluate e modo build
[ ] 6. nodes/job_analyzer.py
[ ] 7. nodes/gap_analyzer.py        — validar score end-to-end até aqui
[ ] 8. nodes/quick_feedback.py
[ ] 9. skills/cv-rewriter/SKILL.md
[ ] 10. agents/career_consultant.py  — testar DeepAgent isolado
[ ] 11. nodes/report_generator.py + tools/cv_formatter.py
[ ] 12. graph/workflow.py            — montar grafo completo, testar router
[ ] 13. app.py                       — UI Streamlit
[ ] 14. Teste de ponta a ponta com CV real + vaga real
```

---

## Requisitos obrigatórios — checklist

| Requisito do enunciado | Onde está |
|---|---|
| LangGraph workflow ≥ 3 nodes | `input_processor` → `job_analyzer` → `gap_analyzer` → `career_consultant`/`quick_feedback` → `report_generator` |
| Router / conditional edge | `route_by_score` em `workflow.py` |
| Multiple tools | `parse_cv`, `extract_job_requirements`, `score_cv`, `format_cv`, `TavilySearch` |
| DeepAgent | `career_consultant.py` via `create_deep_agent` |
| SKILL usado pelo DeepAgent | `skills/cv-rewriter/SKILL.md` com `FilesystemBackend` |
| Problema real | ATS rejection, CVs genéricos, falta de orientação para candidatos |
