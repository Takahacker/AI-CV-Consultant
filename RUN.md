# RUN.md — Como rodar o AI CV Consultant

Guia prático para subir o projeto do zero e validar o fluxo completo.

---

## 1. Pré-requisitos

- **Python 3.11+** (testado em 3.11/3.13 no Windows)
- **pip** atualizado
- Contas/keys nos serviços abaixo (todas têm tier gratuito):
  - **NVIDIA NIM** — `NVIDIA_API_KEY` (https://build.nvidia.com/)
  - **Tavily** — `TAVILY_API_KEY` (https://app.tavily.com/)
  - **LangSmith** *(opcional, só para tracing)* — `LANGCHAIN_API_KEY` (https://smith.langchain.com/)

---

## 2. Setup (uma vez)

```powershell
# A partir da raiz do projeto:
cd c:\Users\kikep\OneDrive\Documentos\7Sem\LLM\AI-CV-Consultant

# (recomendado) ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar dependências
python -m pip install -r requirements.txt
```

Depois, copie o template de variáveis e preencha com as suas chaves:

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` deve ficar assim:

```ini
NVIDIA_API_KEY=nvapi-...
NVIDIA_MODEL=meta/llama-3.3-70b-instruct      # ou meta/llama-4-maverick-17b-128e-instruct
TAVILY_API_KEY=tvly-...

# Opcional — LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=AI-CV-Consultant
```

---

## 3. Rodar a aplicação

```powershell
streamlit run app.py
```

O Streamlit abre o navegador em `http://localhost:8501`. Na UI:

1. **Sidebar** — escolha o modo:
   - *Tenho um CV — quero avaliar/adaptar* (`evaluate`)
   - *Não tenho CV — quero construir do zero* (`build`)
2. **Coluna esquerda** — cole o CV (modo evaluate) ou o dump livre da sua trajetória (modo build).
3. **Coluna direita** — cole a descrição da vaga.
4. Clique em **🚀 Analisar**.

O grafo executa: `input_processor → job_analyzer → gap_analyzer → (router) → quick_feedback OU career_consultant → report_generator`.

Resultado: score 0–100, relatório markdown e CV revisado (download `.md`).

---

## 4. Sanity check rápido (sem rodar a UI)

Cole isso num terminal — compila o grafo e lista os nós/arestas, sem gastar tokens:

```powershell
python -c "from graph.workflow import cv_graph; g = cv_graph.get_graph(); print('Nodes:', list(g.nodes)); print('Edges:', [(e.source, e.target, 'cond' if e.conditional else 'fixed') for e in g.edges])"
```

Saída esperada (6 nós úteis + start/end, 8 arestas, sendo 2 condicionais saindo de `gap_analyzer`):

```
Nodes: ['__start__', 'input_processor', 'job_analyzer', 'gap_analyzer', 'quick_feedback', 'career_consultant', 'report_generator', '__end__']
Edges: [('__start__','input_processor','fixed'), ('career_consultant','report_generator','fixed'), ('gap_analyzer','career_consultant','cond'), ('gap_analyzer','quick_feedback','cond'), ('input_processor','job_analyzer','fixed'), ('job_analyzer','gap_analyzer','fixed'), ('quick_feedback','report_generator','fixed'), ('report_generator','__end__','fixed')]
```

---

## 5. Smoke test ponta-a-ponta (gasta tokens NVIDIA + Tavily)

```powershell
python -c "from graph.workflow import cv_graph; r = cv_graph.invoke({'mode':'evaluate','raw_input':'Joao Silva, Python dev 3y, FastAPI, Docker, AWS. CS degree.','job_description':'Senior Python Backend Engineer. Required: Python, Django, AWS, PostgreSQL. Nice: Kubernetes.','parsed_cv':{},'job_requirements':{},'score':0,'gaps':[],'revised_cv':'','iterations':0,'final_report':''}); print('SCORE:', r['score']); print('GAPS:', r['gaps']); print(r['final_report'][:400])"
```

Esperado: imprime score, gaps e início do relatório. Se score < 80, o DeepAgent (`career_consultant`) entrou em ação e fez web search via Tavily.

---

## 6. Checklist dos requisitos do enunciado

| Requisito | Onde está | Status |
|---|---|---|
| LangGraph workflow ≥ 3 nodes | 5 nós úteis em [graph/workflow.py](graph/workflow.py) | ✅ |
| Router / conditional edge | `_route_by_score` em [graph/workflow.py:13-16](graph/workflow.py#L13-L16) | ✅ |
| Multiple tools | `parse_cv`, `extract_job_requirements`, `score_cv`, `format_cv`, `TavilySearch` em [tools/](tools/) | ✅ |
| DeepAgent | `create_deep_agent` em [agents/career_consultant.py](agents/career_consultant.py) | ✅ |
| SKILL usado pelo DeepAgent | [skills/cv-rewriter/SKILL.md](skills/cv-rewriter/SKILL.md) carregado via `skills=["/skills/"]` | ✅ |
| Problema real | ATS rejeita CVs genéricos antes de chegar ao recrutador (ver [ARCHITECTURE.md](ARCHITECTURE.md)) | ✅ |

---

## 7. Estrutura do projeto

```
AI-CV-Consultant/
├── app.py                       # UI Streamlit
├── .env / .env.example          # API keys
├── requirements.txt
├── ARCHITECTURE.md              # Decisões de design
├── RUN.md                       # Este arquivo
│
├── graph/
│   ├── state.py                 # CVState (TypedDict)
│   └── workflow.py              # StateGraph + router
│
├── nodes/
│   ├── input_processor.py       # Node 1
│   ├── job_analyzer.py          # Node 2
│   ├── gap_analyzer.py          # Node 3
│   ├── quick_feedback.py        # Node 4a (score ≥ 80)
│   └── report_generator.py      # Node 5
│
├── agents/
│   └── career_consultant.py     # Node 4b — DeepAgent (score < 80)
│
├── skills/
│   └── cv-rewriter/SKILL.md     # Skill usado pelo DeepAgent
│
├── tools/
│   ├── cv_parser.py             # @tool parse_cv
│   ├── job_extractor.py         # @tool extract_job_requirements
│   ├── cv_scorer.py             # @tool score_cv
│   └── cv_formatter.py          # @tool format_cv
│
└── config/
    └── settings.py              # init do ChatNVIDIA + thresholds
```

---

## 8. Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'langchain_nvidia_ai_endpoints'` | deps não instaladas | `python -m pip install -r requirements.txt` |
| `KeyError: 'NVIDIA_API_KEY'` ao subir | `.env` faltando ou env var não carregada | Copie `.env.example → .env` e preencha; rode do mesmo diretório |
| `401 Unauthorized` na primeira chamada NVIDIA | chave inválida ou expirada | Gere nova chave em https://build.nvidia.com/ |
| `Tavily 429 / quota exceeded` | tier free do Tavily estourou | Aguarde reset diário ou use outra chave |
| App roda mas score sempre 0 | LLM devolveu JSON malformado | Veja o stack no terminal do streamlit; o fallback regex em `score_cv` tenta recuperar, mas se o modelo estiver muito ruim troque para `meta/llama-3.3-70b-instruct` |
| DeepAgent demora muito (>2 min) | Tavily + múltiplas iterações de reescrita | Reduza `MAX_ITERATIONS` em [config/settings.py](config/settings.py#L16) ou aumente `SCORE_THRESHOLD` |
| `FilesystemBackend virtual_mode deprecation warning` | versão antiga sem `virtual_mode=True` | Já corrigido em [agents/career_consultant.py:16](agents/career_consultant.py#L16) |

---

## 9. O que cada peça faz (resumo de 1 linha)

- **`input_processor`** — texto bruto → CV estruturado (`parse_cv` no modo evaluate, LLM direto no modo build)
- **`job_analyzer`** — descrição da vaga → `{keywords, must_have, nice_to_have, seniority, role_title}`
- **`gap_analyzer`** — compara CV vs vaga via `score_cv` → score 0–100 + lista de gaps
- **Router `_route_by_score`** — score ≥ 80 → caminho rápido; senão → DeepAgent
- **`quick_feedback`** — sugestões leves quando o CV já está bom (não reescreve)
- **`career_consultant` (DeepAgent)** — usa SKILL `cv-rewriter` + Tavily + `score_cv` + `format_cv` em loop iterativo (até 3 iterações)
- **`report_generator`** — consolida tudo em relatório Markdown final
