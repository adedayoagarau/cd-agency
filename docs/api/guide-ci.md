# Guide: Integrating with CI/CD

> Automate content quality checks in your build pipeline.

## Overview

CD Agency's scoring tools (readability, lint, a11y) run offline and return
structured JSON output — perfect for CI/CD integration. No API key is needed
for scoring.

## GitHub Actions Example

```yaml
name: Content Quality Check
on: [push, pull_request]

jobs:
  content-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install CD Agency
        run: pip install -e .

      - name: Score content
        run: |
          cd-agency score all -f content/strings.txt --json-output > report.json
          # Check overall pass
          PASS=$(python -c "import json; print(json.load(open('report.json'))['overall_pass'])")
          if [ "$PASS" != "True" ]; then
            echo "Content quality check failed!"
            cd-agency score all -f content/strings.txt
            exit 1
          fi
```

## Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Find changed content files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(txt|md)$')

if [ -z "$FILES" ]; then
  exit 0
fi

echo "Running content quality checks..."

for file in $FILES; do
  RESULT=$(cd-agency score all -f "$file" --json-output 2>/dev/null)
  PASS=$(echo "$RESULT" | python -c "import sys,json; print(json.load(sys.stdin)['overall_pass'])")
  if [ "$PASS" != "True" ]; then
    echo "FAIL: $file"
    cd-agency score all -f "$file"
    exit 1
  fi
done

echo "All content checks passed."
```

## Python Script for CI

```python
#!/usr/bin/env python3
"""CI content quality gate."""

import json
import sys
from pathlib import Path

from tools.scoring import ReadabilityScorer
from tools.linter import ContentLinter
from tools.a11y_checker import A11yChecker
from tools.report import ScoringReport

def check_file(filepath: Path) -> bool:
    text = filepath.read_text(encoding="utf-8")
    report = ScoringReport(
        text=text,
        readability=ReadabilityScorer().score(text),
        lint_results=ContentLinter().lint(text),
        a11y_result=A11yChecker().check(text),
    )
    if not report.overall_pass:
        print(f"FAIL: {filepath}")
        print(json.dumps(report.to_dict(), indent=2))
        return False
    return True

files = list(Path("content").glob("*.txt"))
results = [check_file(f) for f in files]

if not all(results):
    sys.exit(1)
print(f"All {len(files)} files passed.")
```

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | All checks passed |
| `1` | One or more checks failed |

## Thresholds

Customize thresholds via the Python API:

```python
# Custom readability target
checker = A11yChecker(target_grade=6.0)  # Stricter than default 8.0

# Custom character limits
linter = ContentLinter(max_button_chars=25, max_notification_chars=100)

# Custom jargon list
linter = ContentLinter(custom_jargon=["synergy", "leverage"])
```

## PR Comment Integration

Generate Markdown for PR comments:

```bash
cd-agency score all -f content.txt --markdown | gh pr comment --body-file -
```
