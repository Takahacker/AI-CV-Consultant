# Prompt for Claude: Revise the AI CV Consultant HTML Presentation

You previously generated `ai-cv-consultant-presentation.html` from the brief in `PRESENTATION_PROMPT.md`. The overall design system (palette, typography, slide layout, navigation) is good and must be **preserved**. However, several slides contain inaccuracies and the architecture diagram fails to communicate the most important parts of the system. Apply the corrections below and re-emit the full HTML file.

---

## Part 1: Critical Redesign of Slide 4 (Architecture)

### Why the current diagram is weak

The current SVG shows six boxes connected by arrows and a router diamond. It looks like a generic flowchart and **fails to show the things the rubric actually grades**:

1. **Which tools each node calls.** The five tools (`parse_cv`, `extract_job_requirements`, `score_cv`, `format_cv`, `web_search`) are invisible. From the diagram alone, a viewer cannot tell that the project has "multiple tools".
2. **Where the SKILL plugs in.** `cv-rewriter/SKILL.md` is the only artifact that demonstrates the SKILLS requirement, and it does not appear anywhere on the diagram.
3. **The DeepAgent's internal loop.** The most important behavior of the project is the `research -> rewrite -> score -> loop back` cycle inside `career_consultant`. The current diagram shows it as a single static box, identical to the deterministic nodes.
4. **No loopback arrow.** There is no visual indication that `career_consultant` iterates up to 3 times before exiting.
5. **No external API boundary.** Tavily (web) and NVIDIA NIM (LLM) are not represented, so the viewer cannot reason about where the system meets the outside world.

### Required redesign

Replace the SVG on slide 4 with a **two-zone diagram**. Keep the slide layout (eyebrow, h2, legend, footer) identical to the rest of the deck.

**Zone A: Top horizontal pipeline (the LangGraph workflow)**

Left to right: `START` -> `input_processor` -> `job_analyzer` -> `gap_analyzer` -> **router diamond** -> two outgoing arrows.

Under each deterministic node, render a small horizontal row of **tool chips** showing which tool that node invokes. Use the same `--accent-soft` background and `JetBrains Mono` styling as the existing tool chips elsewhere in the deck:

- Under `input_processor`: chip labeled `parse_cv`
- Under `job_analyzer`: chip labeled `extract_job_requirements`
- Under `gap_analyzer`: chip labeled `score_cv`
- Under `quick_feedback` (in Zone B): chip labeled `format_cv`
- Under `report_generator` (in Zone B): chip labeled `format_cv`

The router diamond has two labeled outgoing arrows:
- Upper branch labeled `score >= 80` going to `quick_feedback`
- Lower branch labeled `score < 80` going to `career_consultant`

**Zone B: Bottom area, split into two columns**

Left column: a small `quick_feedback` box with its `format_cv` tool chip below.

Right column: an enlarged **DeepAgent "engine room"** — a dark rounded card with a `DEEPAGENT` badge at the top. Inside this card, draw three smaller sub-nodes arranged in a horizontal loop:

`web_search` -> `rewrite (LLM)` -> `score_cv`

Then draw a curved arrow returning from `score_cv` back to `web_search` labeled `if score < 80 and iter < 3`. This is the loopback that is missing today. Below the three sub-nodes, draw a horizontal arrow leaving the card labeled `else: exit with revised CV`.

On the right side of the DeepAgent card, draw a small document icon labeled `SKILL.md` with a dashed line connecting it into the DeepAgent. Label the dashed line `loaded via FilesystemBackend(skills=["/skills/"])`. Below the SKILL document, list the SKILL's three tools as chips: `web_search`, `score_cv`, `format_cv`.

Both `quick_feedback` and the DeepAgent card converge into a final `report_generator` node, which connects to `END`.

**Zone C: External boundary annotations**

Two small annotations off to the side, drawn as faded labels with arrows pointing into the relevant nodes:

- `NVIDIA NIM` (LLM API) -> pointing at any node that calls `llm_invoke()` (use a generic label "all LLM calls")
- `Tavily Search API` -> pointing at the `web_search` chip inside the DeepAgent card

**Legend update**

Replace the current legend with:

- Deterministic node (white box)
- DeepAgent (dark card)
- Conditional router (blue diamond)
- Tool chip (light blue pill)
- SKILL (document icon, dashed connection)
- Loopback arrow (curved, labeled with stop condition)

**Implementation note**

Use one inline SVG of roughly 1100 x 560. Keep stroke weights consistent with the current diagram (1.5 to 1.8). The loopback arrow must be visually obvious. The SKILL document icon should be a small rectangle with a folded-corner triangle, not a generic box.

---

## Part 2: Factual Corrections Across the Deck

### Slide 5 (LangGraph Details)

The `CVState` code block uses wrong field names. The actual state defined in `graph/state.py` has these exact fields:

```python
class CVState(TypedDict):
    mode: str
    raw_input: str
    job_description: str
    parsed_cv: dict
    job_requirements: dict
    score: int
    gaps: list
    revised_cv: str
    iterations: int
    final_report: str
```

Replace the current state block with these fields, preserving the visual treatment (dark background, syntax colors, comment style).

The `add_conditional_edges` example uses the wrong literal keys. The actual code uses the destination node names directly:

```python
graph.add_conditional_edges(
    "gap_analyzer",
    _route_by_score,
    {
        "quick_feedback":    "quick_feedback",
        "career_consultant": "career_consultant",
    },
)
```

Replace the highlighted blue code block on the right side of the slide accordingly. Keep the same visual treatment (accent-soft background, blue accent left border).

### Slide 2 (Problem)

The three stat tiles (`60-75%`, `2-4h`, `0`) use unsourced numbers that a professor may challenge. Either:

- **Option A (preferred):** soften them. Change "60-75%" to "Most CVs"; change "2-4h" to "Hours per posting"; remove the bottom-row label about junior candidates and replace with "No feedback loop after rejection." Keep the visual layout.
- **Option B:** add a small `Source: industry estimates` footnote in muted text below the stats row.

Pick Option A.

### Slide 7 (Live Demo)

The mockup tabs read `Score / Analysis / Revised CV / Download`. The real Streamlit app uses only two tabs after the score card: `Relatorio de analise` and `Curriculo revisado`. Update the mockup tabs to show exactly two tabs with these Portuguese labels (keep them in Portuguese since the real app is in Portuguese). Mark `Curriculo revisado` as the active tab.

The mockup's `app-sub` line currently reads "Analise seu curriculo contra qualquer vaga". Change to "Avalie e adapte seu curriculo a uma vaga especifica com apoio de IA." to match the actual app subtitle.

### Slide 1 (Title)

The hardcoded date `2026` in the credits block is fine. The `marker` text has a stray period and reads `FINAL PROJECT . LLM AGENT SYSTEMS`. Keep the period style but make sure it reads `FINAL PROJECT . LLM AGENT SYSTEMS . 2026` to match the convention used in `meta` rows.

The H1 currently shows `AI CV Consultant.` with a trailing period. Remove the period; the bar accent already gives it weight.

### Slide 6 (DeepAgent + SKILL)

The right code card shows a fake SKILL.md. Replace the workflow section with the actual workflow used in the real `skills/cv-rewriter/SKILL.md`:

```
## Workflow
1. Read CV, requirements, gaps, current score, iter count
2. web_search ATS keywords and role best practices
3. Rewrite bullets: action verbs + quantified results
4. Naturally include missing must-have keywords
5. Call score_cv to evaluate
6. If score < 80 and iter < 3, loop from step 2
7. Call format_cv for final markdown
8. Return JSON: revised_cv, score, iterations, changes_summary
```

Keep the YAML frontmatter visual style identical.

### Slide 8 (Challenges)

Challenge 02 mentions exponential backoff "3, 6, 12, 24, 48s" — keep this. Verify all five challenge cards plus the meta-lesson card retain identical card styling.

---

## Part 3: Design System Rules to Preserve

- 16:9 slide layout, max-width center alignment
- Palette: `#fafbfc` background, `#0f172a` ink, `#2563eb` accent, `#dbeafe` accent-soft
- Typography: Inter sans, JetBrains Mono for code
- Navigation: arrow keys, space bar, F for fullscreen, click halves
- No emojis. No em or en dashes anywhere. Use periods, colons, or plain hyphens.
- Slide counter and progress bar must stay
- Animations and transitions must stay

---

## Output

Re-emit the **entire HTML file** with the above corrections applied. Do not summarize the changes. Do not produce a diff. Produce the complete updated `ai-cv-consultant-presentation.html` ready to open in a browser.
