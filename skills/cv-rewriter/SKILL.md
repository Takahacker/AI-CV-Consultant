---
name: cv-rewriter
description: Use this skill when asked to rewrite a CV to better match a specific job description. Includes web research for current market standards and iterative scoring until the target score is reached.
---

# cv-rewriter

## Goal
Rewrite CV sections using results-oriented language aligned with the target job's keywords and current market expectations.

## Workflow
1. Read the current CV, job requirements, gaps, current score, and iteration count from the task.
2. Use `TavilySearch` to research:
   - `"best CV bullet points for [role_title] [current year]"`
   - `"ATS keywords for [role_title]"`
   - `"required skills [role_title] job market"`
3. Rewrite experience bullet points:
   - Start each bullet with a strong action verb (Led, Built, Reduced, Improved, etc.)
   - Quantify results wherever possible (%, time saved, revenue impact)
   - Naturally incorporate missing keywords from the gap list
4. Enhance the professional summary to reflect the target role clearly.
5. Add missing must-have skills to the skills section if they are truthfully represented in the experience.
6. Call `score_cv` with the rewritten CV and job requirements.
7. If score < 80 and current iteration < MAX_ITERATIONS, refine further and repeat from step 3.
8. Call `format_cv` to produce the final clean Markdown version.

## Output format
Return a JSON object with:
- `revised_cv` (string): the rewritten CV in clean Markdown
- `score` (integer): the final score after rewriting
- `iterations` (integer): how many rewrite iterations were performed
- `changes_summary` (string): brief description of the main changes made
