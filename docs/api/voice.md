# `tools.voice_checker` — Voice Checker

> Stability: Stable

```python
from tools.voice_checker import VoiceChecker, VoiceProfile, VoiceResult, VoiceDeviation
```

Brand voice consistency checking using LLM scoring or rule-based heuristics.

## Class: `VoiceProfile`

A brand voice configuration.

```python
@dataclass
class VoiceProfile:
    name: str
    tone_descriptors: list[str]
    do_list: list[str]
    dont_list: list[str]
    sample_content: list[str] = field(default_factory=list)
```

### `VoiceProfile.from_yaml(filepath)`

Load a voice profile from a YAML file.

- `filepath`: `str | Path`
- Returns: `VoiceProfile`

```python
profile = VoiceProfile.from_yaml("presets/material-design.yaml")
print(profile.name)  # "Material Design"
```

### `VoiceProfile.from_dict(data)`

Create from a dictionary.

- `data`: `dict`
- Returns: `VoiceProfile`

### `profile.to_prompt()`

Convert to a prompt description for LLM evaluation.

- Returns: `str`

---

## Class: `VoiceDeviation`

A specific phrase that deviates from brand voice.

```python
@dataclass
class VoiceDeviation:
    phrase: str
    reason: str
    suggestion: str
```

---

## Class: `VoiceResult`

Result of voice consistency check.

```python
@dataclass
class VoiceResult:
    score: float              # 1–10
    summary: str
    deviations: list[VoiceDeviation]
    strengths: list[str]
```

### `result.label`

Human-readable score label.

- Type: `str` (property)

| Score | Label |
| --- | --- |
| 9–10 | Excellent |
| 7–8 | Good |
| 5–6 | Needs Work |
| 3–4 | Poor |
| 1–2 | Off-Brand |

### `result.to_dict()`

- Returns: `dict`

---

## Class: `VoiceChecker`

### Constructor

```python
VoiceChecker(
    client=None,
    model: str = "claude-sonnet-4-20250514",
)
```

- `client`: Optional `anthropic.Anthropic` instance. Lazy-initialized if `None`.
- `model`: Model for LLM-based checking.

### `checker.check(text, profile)`

Check text against a voice profile using LLM.

- `text`: `str`
- `profile`: `VoiceProfile`
- Returns: `VoiceResult`
- **Requires:** `ANTHROPIC_API_KEY`

The LLM evaluates the text against the voice guide and returns a structured
score with specific deviations and suggestions.

```python
checker = VoiceChecker()
profile = VoiceProfile.from_yaml("presets/material-design.yaml")
result = checker.check("Click here to see your settings", profile)

print(f"Score: {result.score}/10 ({result.label})")
for d in result.deviations:
    print(f"  - '{d.phrase}': {d.reason}")
    print(f"    Suggestion: {d.suggestion}")
```

### `checker.check_without_llm(text, profile)`

Rule-based voice check using heuristics. No API key needed.

- `text`: `str`
- `profile`: `VoiceProfile`
- Returns: `VoiceResult`

Checks the text against the profile's `do_list` and `dont_list`:

- Each violated "don't" rule deducts 1 point from a starting score of 10.
- Each matched "do" rule is recorded as a strength.
- Score is clamped to 1–10.

```python
result = checker.check_without_llm("Click here to see details", profile)
print(f"Score: {result.score}/10")
print(f"Summary: {result.summary}")
```
