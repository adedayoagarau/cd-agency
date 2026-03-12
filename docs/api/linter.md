# `tools.linter` — Content Linter

> Stability: Stable

```python
from tools.linter import ContentLinter, LintResult, LintSeverity
```

Automated content quality checks. No API key required.

## Enum: `LintSeverity`

```python
class LintSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

## Class: `LintResult`

Result of a single lint rule check.

```python
@dataclass
class LintResult:
    rule: str
    passed: bool
    severity: LintSeverity
    message: str
    suggestion: str = ""
    matches: list[str] = field(default_factory=list)
```

### `result.to_dict()`

- Returns: `dict` with keys: `rule`, `passed`, `severity`, `message`, and
  optionally `suggestion` and `matches`.

---

## Class: `ContentLinter`

### Constructor

```python
ContentLinter(
    custom_jargon: list[str] | None = None,
    custom_exclusionary: dict[str, str] | None = None,
    max_button_chars: int = 40,
    max_notification_chars: int = 120,
    prefer_consistency: bool = False,
)
```

- `custom_jargon`: Additional jargon words to flag.
- `custom_exclusionary`: Additional exclusionary terms (term → replacement).
- `max_button_chars`: Maximum allowed characters for button text.
- `max_notification_chars`: Maximum allowed characters for notification text.
- `prefer_consistency`: When `True`, character-limit checks get a 20% headroom
  buffer and violations are downgraded from *error* to *info*. Use this when
  keeping parallel strings consistent (e.g., a row of buttons or a set of menu
  items) is more important than strict brevity.

### `linter.lint(text, content_type)`

Run applicable lint rules on text.

- `text`: `str`
- `content_type`: `str` — One of `"general"`, `"cta"`, `"button"`, `"error"`,
  `"notification"`, `"microcopy"`.
- Returns: `list[LintResult]`

```python
linter = ContentLinter()
results = linter.lint("Click here to learn more!", content_type="button")
for r in results:
    if not r.passed:
        print(f"[{r.severity.value}] {r.rule}: {r.message}")
        if r.suggestion:
            print(f"  -> {r.suggestion}")
```

### Rules by Content Type

| Rule | general | cta | button | error | notification | microcopy |
| --- | --- | --- | --- | --- | --- | --- |
| `no-jargon` | x | x | x | x | x | x |
| `inclusive-language` | x | x | x | x | x | x |
| `no-passive-voice` | x | x | x | x | x | x (2x) |
| `cta-action-verb` | | x | x | | | |
| `button-char-limit` | | x | x | | | |
| `error-actionable` | | | | x | | |
| `notification-char-limit` | | | | | x | |

### `linter.lint_all(text)`

Run all rules regardless of content type.

- Returns: `list[LintResult]`

Includes all rules plus `consistent-terminology`.

---

## Lint Rules Reference

### `no-jargon` (warning)

Flags buzzwords and corporate jargon.

**Default jargon list (28 terms):** `leverage`, `utilize`, `facilitate`,
`synergy`, `paradigm`, `scalable`, `robust`, `seamless`, `cutting-edge`,
`best-in-class`, `end-to-end`, `mission-critical`, `value-add`, `ecosystem`,
`bandwidth`, `circle back`, `deep dive`, `move the needle`,
`low-hanging fruit`, `boil the ocean`, `bleeding edge`, `disrupt`, `pivot`,
`iterate`, `align`, `incentivize`, `operationalize`, `actualize`, `ideate`.

Custom jargon can be added via the constructor.

### `inclusive-language` (error)

Flags exclusionary terms and suggests replacements.

| Term | Replacement |
| --- | --- |
| `whitelist` | `allowlist` |
| `blacklist` | `blocklist` |
| `master` | `main/primary` |
| `slave` | `replica/secondary` |
| `dummy` | `placeholder/sample` |
| `sanity check` | `quick check/smoke test` |
| `grandfathered` | `legacy/exempt` |
| `guys` | `everyone/team/folks` |
| `manpower` | `workforce/staffing` |
| `man-hours` | `person-hours/work hours` |
| `cripple` | `disable/limit` |
| `lame` | `inadequate/insufficient` |
| `crazy` | `unexpected/surprising` |
| `insane` | `extreme/intense` |

### `no-passive-voice` (warning)

Detects passive voice patterns like "was sent", "has been saved", "will be
deleted".

### `cta-action-verb` (error)

CTA text must start with an action verb. Checks against 48 common action verbs
including: `get`, `start`, `try`, `create`, `join`, `explore`, `discover`,
`learn`, `download`, `sign`, `save`, `submit`, `buy`, `book`, `share`, etc.

### `button-char-limit` (error)

Button text must be ≤ 40 characters (configurable).

### `notification-char-limit` (error)

Notification text must be ≤ 120 characters (configurable).

### `error-actionable` (error)

Error messages must contain resolution/action language (e.g., "try", "check",
"ensure", "retry", "contact", "refresh", "you can", "to fix").

### `consistent-terminology` (warning)

Detects mixed terminology within the same text:

- `log in` / `login`
- `sign up` / `signup`
- `e-mail` / `email`
- `set up` / `setup`
- `check out` / `checkout`
