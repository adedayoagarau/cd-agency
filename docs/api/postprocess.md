# `runtime.postprocess` — Auto-Validation

> Stability: Experimental

```python
from runtime.postprocess import extract_fragments, postprocess_output, ContentFragment, PostprocessResult
```

Validates agent output against UI constraints automatically. After an agent
generates content, this module extracts labeled text fragments (e.g.,
`**Button:** Save Changes`) and validates each against character limits,
platform conventions, localization expansion, and accessibility rules.

## How It Works

1. **Extract** — Scans agent output for labeled content patterns like
   `**Button:** Save`, `**Toast:** Changes saved`, `**Error:** Invalid email`
2. **Validate** — Checks each fragment against its element type's constraints
   (character limit, a11y, localization expansion factor)
3. **Report** — Returns a `PostprocessResult` with all fragments and their
   validation results

## Class: `ContentFragment`

A piece of content extracted from agent output.

```python
@dataclass
class ContentFragment:
    text: str           # The extracted text
    element_type: str   # e.g., "button", "toast", "inline_error"
    source_label: str   # The original label from agent output
```

## Class: `PostprocessResult`

```python
@dataclass
class PostprocessResult:
    fragments: list[ContentFragment]
    validations: list[tuple[ContentFragment, ConstraintResult]]
```

### Properties

- `has_issues` — `True` if any validation failed
- `issues` — List of `(fragment, result)` pairs that failed
- `summary` — Human-readable summary of all validation results

## Functions

### `extract_fragments(output_text, agent_slug=None)`

Extract labeled content fragments from agent output text.

- `output_text`: `str` — Raw agent output
- `agent_slug`: `str | None` — Agent slug for fallback element-type mapping
- Returns: `list[ContentFragment]`

### `postprocess_output(agent, output, platform=None)`

Run full post-processing: extract fragments and validate each one.

- `agent`: `Agent` — The agent that produced the output
- `output`: `AgentOutput` — The agent's output
- `platform`: `str | None` — Target platform (`"ios"`, `"android"`, `"web"`)
- Returns: `PostprocessResult`

## Supported Element Types

| Element | Default Char Limit |
| --- | --- |
| `button` | 40 |
| `tooltip` | 150 |
| `toast` | 50 |
| `push_title` | 65 |
| `push_body` | 240 |
| `modal_headline` | 60 |
| `modal_body` | 300 |
| `inline_error` | 80 |
| `placeholder` | 50 |
| `form_label` | 30 |
| `badge` | 15 |
| `tab_label` | 20 |
| `nav_label` | 25 |
| `sms` | 160 |

## CLI Usage

```bash
# Auto-validate after an agent run
cd-agency agent run error -i "Payment failed" --validate

# Validate for a specific platform
cd-agency agent run mobile -i "Saved" --validate --platform ios
```
