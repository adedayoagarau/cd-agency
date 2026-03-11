# Guide: Scoring Your Content

> A practical guide to using CD Agency's offline scoring tools.

## Overview

CD Agency provides three scoring tools that run entirely offline — no API key
needed:

| Tool | What It Checks |
| --- | --- |
| **Readability** | Flesch-Kincaid grade, reading ease, sentence complexity |
| **Lint** | Jargon, inclusive language, passive voice, CTA verbs, char limits |
| **Accessibility** | WCAG compliance — reading level, link text, ALL CAPS, alt text |

## Quick Score

Run all three at once:

```bash
cd-agency score all -i "Your text here"
```

## Scoring Workflow

### 1. Start with Readability

```bash
cd-agency score readability -i "We're excited to announce that we have successfully implemented a new feature that allows you to seamlessly manage your account settings."
```

**Result:** Grade 14.2 (college level) — too complex for most UI copy.

### 2. Rewrite and Compare

```bash
cd-agency score readability \
  -i "Manage your account settings from one place." \
  -c "We're excited to announce that we have successfully implemented a new feature that allows you to seamlessly manage your account settings."
```

**Result:** Grade dropped from 14.2 to 4.8. Word count dropped from 22 to 7.

### 3. Lint for Quality

```bash
cd-agency score lint -i "Manage your account settings from one place."
```

### 4. Check Accessibility

```bash
cd-agency score a11y -i "Manage your account settings from one place."
```

### 5. Check Voice (Optional)

```bash
cd-agency score voice \
  -i "Manage your account settings from one place." \
  --guide presets/material-design.yaml --no-llm
```

## Content Type-Specific Scoring

### Buttons and CTAs

```bash
cd-agency score lint -i "Get started" --type button
# Checks: action verb, character limit (40), jargon, inclusive, passive

cd-agency score lint -i "Click here to learn more" --type button
# FAIL: cta-action-verb — "click" is not in the action verb list
```

### Error Messages

```bash
cd-agency score lint -i "Something went wrong" --type error
# FAIL: error-actionable — no resolution guidance

cd-agency score lint -i "Something went wrong. Try refreshing the page." --type error
# PASS: Contains "try refreshing" (resolution language)
```

### Notifications

```bash
cd-agency score lint -i "Your order has shipped! Track it in the app." --type notification
# Checks: character limit (120), jargon, inclusive, passive
```

## JSON Output for CI/CD

```bash
cd-agency score all -i "Your text" --json-output > report.json
```

Parse with `jq`:

```bash
cd-agency score all -i "Save" --json-output | jq '.overall_pass'
# true
```

## Markdown Output for PRs

```bash
cd-agency score all -i "Your text" --markdown >> pr-comment.md
```

## Batch Scoring from Files

```bash
cd-agency score all -f content.txt
```

## Python API

```python
from tools.scoring import ReadabilityScorer
from tools.linter import ContentLinter
from tools.a11y_checker import A11yChecker
from tools.report import ScoringReport, ReportFormat

text = "Click here to learn more about our features"

report = ScoringReport(
    text=text,
    readability=ReadabilityScorer().score(text),
    lint_results=ContentLinter().lint(text, content_type="button"),
    a11y_result=A11yChecker().check(text),
)

# Programmatic access
if not report.overall_pass:
    print("Content needs improvement")
    for r in report.lint_results:
        if not r.passed:
            print(f"  [{r.severity.value}] {r.rule}: {r.suggestion}")

# Render as text, JSON, or Markdown
print(report.render(ReportFormat.MARKDOWN))
```

## Recommended Targets

| Metric | Target | Why |
| --- | --- | --- |
| Flesch-Kincaid Grade | ≤ 8 | WCAG 3.1.5 reading level |
| Sentence length | ≤ 20 words | Comprehension sweet spot |
| Button text | ≤ 40 chars | Fits mobile screens |
| Notification text | ≤ 120 chars | Visible without truncation |
| Complexity index | ≤ 0.10 | Minimal 3+ syllable words |
