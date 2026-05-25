# Prompt for Claude: Build an HTML Presentation for "AI CV Consultant"

## Task

Generate a polished, self-contained **HTML presentation** for an oral final-project pitch in a course on **LLM-based agent systems** (LangChain, LangGraph, DeepAgents, SKILLS). The presentation lasts **5 to 10 minutes** and must cover every item in the rubric below. Deliver one HTML file with inline CSS (no external assets) using a clean, minimal design system (neutral palette: slate/white, single accent color; Inter or system sans-serif; generous whitespace; 16:9 slides; no emojis; no em or en dashes; arrow-key navigation between slides).

The presenter is a student. Audience is the professor and classmates with technical context. Tone: confident, technical, focused on decisions and trade-offs, not marketing speak.

---

## Project Summary (use this as the source of truth)

**Name:** AI CV Consultant
**Repository structure:** Streamlit front-end + LangGraph workflow + DeepAgent + skill.
**Stack:**
- Orchestration: LangGraph (`StateGraph`) + LangChain (`@tool` decorator)
- LLM: NVIDIA NIM via `langchain_nvidia_ai_endpoints.ChatNVIDIA` (model `meta/llama-3.3-70b-instruct`)
- Web search: Tavily via `langchain_tavily.TavilySearch`, wrapped in a custom `@tool`
- DeepAgent: `deepagents.create_deep_agent` with `FilesystemBackend(virtual_mode=True)` and a SKILL loaded from disk
- UI: Streamlit (PDF upload + plain text input)
- Optional tracing: LangSmith

---

## The Real Problem (Slide content)

Generic CVs are filtered out by **ATS (Applicant Tracking Systems)** before any recruiter reads them. Candidates do not know which keywords are missing, which sections are weak, or how to rephrase experience for a specific role. Manual tailoring takes hours per application and most applicants simply submit the same CV everywhere.

Why it matters:
- ATS rejects 60 to 75 percent of CVs in many industries before human review
- Junior candidates and career switchers lack feedback loops
- Every job posting demands different keywords and emphasis

---

## The Proposed Solution

A workflow-driven AI consultant that takes a candidate's CV (PDF or text) plus a job description and returns:
1. An ATS-style score from 0 to 100
2. A list of concrete gaps
3. A rewritten CV tailored to that specific job
4. A markdown report with action items

Two operating modes:
- **Evaluate:** user pastes or uploads an existing CV
- **Build:** user dumps free-form career notes, the system structures them into a CV first

---

## Architecture (Slide content)

A LangGraph `StateGraph` with **6 nodes** and a **conditional router**. State is a shared `CVState` TypedDict that every node mutates.

```
START
  v
input_processor      Node 1: parse PDF or text into structured CV dict
  v
job_analyzer         Node 2: extract keywords, must_have, nice_to_have, seniority
  v
gap_analyzer         Node 3: compute score (0-100) and list gaps
  v
[router: route_by_score]
  |                                  |
  v score >= 80                      v score < 80
quick_feedback                  career_consultant   <-- DeepAgent loop
(light suggestions)             (research + rewrite + score, up to 3 iters)
  |                                  |
  +------> report_generator <--------+
                v
              END
```

The **router** is implemented as `add_conditional_edges("gap_analyzer", route_by_score, {...})` and is the entire reason the system has two execution paths. High-scoring CVs save tokens by skipping the DeepAgent.

---

## Tools (multiple, as required by the rubric)

All exposed via `@tool` decorator from `langchain_core.tools`:

| Tool | Purpose |
|------|---------|
| `parse_cv(raw_text)` | Raw CV text or PDF-extracted text into structured dict (name, summary, experience, skills, education) |
| `extract_job_requirements(job_description)` | Job description into `{role_title, seniority, keywords, must_have, nice_to_have}` |
| `score_cv(parsed_cv, job_requirements)` | Returns `{score, gaps, matched_keywords, suggestions}` |
| `format_cv(cv_data)` | Renders structured CV as clean Markdown |
| `web_search(query)` | Thin wrapper over `TavilySearch`; exposed to the DeepAgent for market research |

The `web_search` wrap is intentional. The raw `TavilySearch` tool exposes optional args (`include_domains`, `exclude_domains`, `time_range`) that the LLM kept serializing incorrectly (`'[]'` as a string instead of `[]`), causing pydantic validation errors. Wrapping reduced the tool surface to `query: str` and eliminated that class of error.

---

## DeepAgent (`career_consultant`)

Created with `deepagents.create_deep_agent`:

```python
_agent = create_deep_agent(
    model=llm,
    tools=[web_search, score_cv, format_cv],
    backend=FilesystemBackend(root_dir=".", virtual_mode=True),
    skills=["/skills/"],
    system_prompt="...senior career consultant...use cv-rewriter skill...iterate until score >= 80 or 3 iterations..."
)
```

It executes a research-then-rewrite-then-score loop with up to 3 iterations. The agent is invoked only when the deterministic `gap_analyzer` reports a score below 80. The loop terminates early on success.

---

## SKILL (`cv-rewriter`)

Stored at `skills/cv-rewriter/SKILL.md`, loaded via the `skills=["/skills/"]` parameter using the `FilesystemBackend`. The SKILL is a markdown file with YAML frontmatter (`name`, `description`) followed by a structured workflow that tells the DeepAgent:

1. Read the current CV, job requirements, gaps, and iteration count
2. Use `web_search` to research ATS keywords and role best practices
3. Rewrite experience bullets with action verbs and quantified results
4. Naturally incorporate missing keywords
5. Call `score_cv` to evaluate
6. If below threshold and iterations left, loop
7. Call `format_cv` to produce the final Markdown CV
8. Return a JSON with `revised_cv`, `score`, `iterations`, `changes_summary`

The SKILL is what makes the DeepAgent reusable and inspectable. It is content, not code, so it can be edited without touching Python.

---

## Live Demo (what to show)

Streamlit app at `localhost:8501`:
1. Choose mode (already have a CV vs. build from scratch)
2. Upload a real PDF resume (the pypdf-extracted text is shown in an expander)
3. Paste a real job description from LinkedIn
4. Click "Analisar curriculo"
5. Show the score card, status, the analysis report tab, the revised CV tab with download button
6. Optionally open LangSmith and walk through the trace to show every node and tool call

Have one pre-recorded run as a fallback in case the network or NVIDIA NIM rate limit gets in the way during the live demo.

---

## Challenges, Decisions, Lessons (this is what graders weight heavily)

**Challenge 1: LLM-generated tool arguments are noisy.**
TavilySearch failed with pydantic errors because the model serialized `include_domains: '[]'` as a string. Fix: wrap external tools with a minimal `@tool` exposing only the arguments the agent actually needs. Lesson: do not assume LLM JSON arguments will match the strict pydantic schema of a third-party tool.

**Challenge 2: NVIDIA NIM free-tier rate limits (HTTP 429).**
The DeepAgent loop multiplies LLM calls. We hit 429s mid-run, raising an exception in `_handle_tool_error`. Fix: `llm_invoke()` wrapper in `config/settings.py` with exponential backoff (3, 6, 12, 24, 48 seconds), applied at every tool and node that calls the LLM. A second retry layer wraps the DeepAgent invocation itself, since `create_deep_agent` binds tools to the raw LLM internally and bypasses our wrapper. Lesson: defense in depth for external APIs; build retries at the boundary where you actually own the call.

**Challenge 3: `deepagents` API stability.**
`FilesystemBackend` issues a deprecation warning when `virtual_mode` is not explicit, and the default flips in 0.6.0. We set `virtual_mode=True` and use absolute virtual paths (`/skills/`) which matches the documented Anthropic skills convention. Lesson: pin or read the changelog for fast-moving libraries.

**Challenge 4: Router design.**
The conditional edge is the cheapest performance win in the project. By short-circuiting strong CVs to `quick_feedback`, we avoid an expensive DeepAgent loop and several Tavily calls when they would not change the outcome. Lesson: not every input needs the full pipeline; route by signal.

**Challenge 5: Two execution modes in one graph.**
Originally `evaluate` and `build` were separate graphs. Collapsing them by branching only inside `input_processor` kept the LangGraph topology clean and made the rest of the pipeline mode-agnostic.

---

## Insights to Share With the Class

- LangGraph shines when you need a deterministic skeleton with selective AI agency. The DeepAgent only runs when the deterministic part flags trouble.
- SKILLS are markdown contracts between humans and agents. They are version-controllable, code-reviewable, and replaceable without redeploying Python.
- A score-based router is a cheap and explainable alternative to letting an agent decide its own path. Use the agent for what it is good at (creative rewriting, research), not for routing.
- Wrapping noisy third-party tools in your own `@tool` is a low-cost reliability win.

---

## Slide Plan (target 9 slides for an 8-minute talk)

1. **Title.** Project name, presenter, course, date.
2. **The Problem.** ATS rejection, generic CVs, tailoring is manual and expensive.
3. **The Solution.** What the system does in one sentence; two input modes; one output bundle (score + report + revised CV).
4. **Architecture Overview.** The graph diagram (use the ASCII diagram or render a nicer SVG version of it). Highlight the router visually.
5. **LangGraph Details.** State, 6 nodes, 1 conditional edge. Mention multiple tools listed in a small table.
6. **The DeepAgent + SKILL.** Show the `create_deep_agent` call and the SKILL.md structure side by side. Explain the rewrite-research-score loop with max 3 iterations.
7. **Live Demo.** Screenshot or live screen share placeholder. List the steps you will perform on stage.
8. **Challenges and Lessons.** The five challenges above, condensed to one line each.
9. **Closing.** What worked, what is next, thanks, questions.

---

## Visual and UX Requirements for the HTML

- Single self-contained HTML file. Inline `<style>`. No CDN, no external fonts that require network. Use `font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif`.
- 16:9 aspect ratio (`1280x720` or `1600x900` reference). Center content with max-width.
- Slide transitions: left and right arrow keys to navigate, plus space bar for next. Optional: `?` for help, `f` for fullscreen.
- Show a small slide counter in the bottom right (e.g., `4 / 9`).
- Use a neutral palette: background `#f8fafc`, text `#0f172a`, accent `#2563eb` or `#0ea5e9`. Borders `#e2e8f0`.
- Typography: titles 2.2 to 2.6 rem bold, body 1.05 rem, code `JetBrains Mono` fallback `monospace`.
- Render the architecture diagram either as inline SVG or as a styled ASCII block with monospace font.
- Code samples should use a subtle background, rounded corners, and syntax-colored manually if possible.
- No emojis anywhere. No em or en dashes. Use periods, colons, or plain hyphens.

---

## Output

Produce one HTML file ready to open in a browser. Include all the content above in slide form, in English, technically precise, no filler. Prioritize density over decoration. The presenter will read aloud from the slides, so each slide must stand alone visually.
