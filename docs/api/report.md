# `tools.report` — Scoring Reports

> Stability: Stable

```python
from tools.report import ScoringReport, ReportFormat
```

Consolidated scoring report generation across all tools.

## Enum: `ReportFormat`

```python
class ReportFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
```

## Class: `ScoringReport`

```python
@dataclass
class ScoringReport:
    text: str
    readability: ReadabilityResult | None = None
    lint_results: list[LintResult] = field(default_factory=list)
    a11y_result: A11yResult | None = None
    voice_result: VoiceResult | None = None
    before_readability: ReadabilityResult | None = None  # For comparison mode
```

### `report.overall_pass`

Overall pass/fail based on all checks.

- Type: `bool` (property)

**Failure conditions:**

- Any lint result with `severity=ERROR` that did not pass.
- Accessibility result with critical or high issues.
- Voice result with score < 5.

### `report.render(fmt)`

Render the report in the specified format.

- `fmt`: `ReportFormat` (default: `TEXT`)
- Returns: `str`

### `report.to_dict()`

Convert report to dictionary.

- Returns: `dict`

```json
{
  "overall_pass": true,
  "readability": { ... },
  "lint": { "passed": true, "results": [...] },
  "accessibility": { "passed": true, ... },
  "voice": { "score": 8.5, ... },
  "comparison": { "before": {...}, "after": {...} }
}
```

### Output Formats

**Text** — Rich terminal output with sections, pass/fail indicators, and
suggestions. Used by default in the CLI.

**JSON** — Machine-readable structured output. Includes all metrics and
individual rule results.

**Markdown** — Table-formatted report suitable for documentation, PRs, or
issue comments. Includes readability table, lint table, a11y table, and voice
summary.

### Comparison Mode

Set `before_readability` to enable before/after comparison:

```python
scorer = ReadabilityScorer()
report = ScoringReport(
    text="Submit",
    readability=scorer.score("Submit"),
    before_readability=scorer.score("Click here to submit your information"),
)
print(report.render(ReportFormat.TEXT))
```

Comparison shows delta for grade level, reading ease, and word count.
