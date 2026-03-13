# Quick Start

> Get productive with CD Agency in 5 minutes.

## 1. Score Content (No API Key Required)

Score any text for readability, lint issues, and accessibility:

```bash
cd-agency score all -i "Click here to submit your information"
```

Output:

```
============================================================
  CONTENT SCORING REPORT
============================================================
  Overall: FAIL

--- Readability ---
  Words: 6  |  Sentences: 1
  Flesch Reading Ease: 59.7 (Standard)
  Flesch-Kincaid Grade: 6.4 (Easy (6th-8th grade))

--- Content Lint ---
  [PASS] no-jargon: No jargon detected
  [PASS] inclusive-language: No exclusionary language detected
  [PASS] no-passive-voice: No passive voice detected

--- Accessibility ---
  [HIGH] descriptive-link-text: Found 'click here' pattern(s)
         WCAG: 2.4.4 Link Purpose
============================================================
```

## 2. Lint a CTA Button

```bash
cd-agency score lint -i "Click here to learn more!" --type button
```

```
  [FAIL] cta-action-verb: CTA should start with an action verb
         -> Try starting with: claim, discover, explore, invite...
```

## 3. Compare Before/After Readability

```bash
cd-agency score readability -i "Submit" -c "Click here to submit your information"
```

```
--- Before/After Comparison ---
  Grade level: 6.4 -> 8.4 (+2.0)
  Reading ease: 59.7 -> 36.6 (-23.1)
  Word count: 6 -> 1 (-5)
```

## 4. Run an Agent (Requires API Key)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

cd-agency agent run error -i "User tries to upload a file larger than 10MB"
```

The Error Message Architect agent returns a complete error message package with
user-facing copy, resolution steps, developer notes, and prevention tips.

## 5. Get JSON Output

Every command supports `--json-output`:

```bash
cd-agency score all -i "Save your work" --json-output
```

```json
{
  "overall_pass": true,
  "readability": {
    "word_count": 3,
    "flesch_reading_ease": 100,
    "flesch_kincaid_grade": 0,
    "grade_label": "Very Easy (5th grade)"
  },
  "lint": { "passed": true, "results": [...] },
  "accessibility": { "passed": true, "issue_count": 0 }
}
```

## 6. Export Content

```bash
cd-agency export -i "Click here" -o "Learn more" --format xliff
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2">
  <file source-language="en" target-language="en">
    <body>
      <trans-unit id="1">
        <source>Click here</source>
        <target>Learn more</target>
      </trans-unit>
    </body>
  </file>
</xliff>
```

## 7. Use as a Python Library

```python
from tools.scoring import ReadabilityScorer
from tools.linter import ContentLinter
from tools.a11y_checker import A11yChecker

# Score readability
scorer = ReadabilityScorer()
result = scorer.score("Your changes have been saved.")
print(f"Grade: {result.flesch_kincaid_grade} ({result.grade_label})")

# Lint content
linter = ContentLinter()
issues = linter.lint("Click here to learn more!", content_type="button")
for issue in issues:
    if not issue.passed:
        print(f"[{issue.severity.value}] {issue.rule}: {issue.message}")

# Check accessibility
checker = A11yChecker()
a11y = checker.check("Click here to see pricing")
print(f"Passed: {a11y.passed} | Issues: {a11y.issue_count}")
```

## Next Steps

- [CLI Reference](cli.md) — All commands and options
- [Python API](agent.md) — Use the SDK programmatically
- [Agents](agents.md) — Browse all 17 agents
- [Workflows](workflows.md) — Multi-agent pipelines
- [Configuration](configuration.md) — Customize behavior
