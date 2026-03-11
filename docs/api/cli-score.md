# `score` Commands

> Stability: Stable

Score and evaluate content quality. All scoring commands work **offline** — no
API key required (except `score voice` without `--no-llm`).

```bash
cd-agency score COMMAND [OPTIONS]
```

## `score readability`

Score text for readability metrics using Flesch-Kincaid formulas.

```bash
cd-agency score readability [OPTIONS]
```

**Options:**

| Option | Short | Type | Description |
| --- | --- | --- | --- |
| `--input` | `-i` | string | Text to score |
| `--file` | `-f` | path | Read from file |
| `--compare` | `-c` | string | "Before" text to compare against |
| `--json-output` | | flag | Output as JSON |

**Metrics returned:**

| Metric | Description |
| --- | --- |
| Word count | Total words |
| Sentence count | Total sentences |
| Flesch Reading Ease | 0–100 scale (higher = easier) |
| Flesch-Kincaid Grade | US grade level |
| Avg sentence length | Words per sentence |
| Complexity index | Ratio of 3+ syllable words |
| Reading time | Estimated reading time at 238 WPM |

**Ease labels:**

| Score | Label |
| --- | --- |
| 90–100 | Very Easy |
| 80–89 | Easy |
| 70–79 | Fairly Easy |
| 60–69 | Standard |
| 50–59 | Fairly Difficult |
| 30–49 | Difficult |
| 0–29 | Very Difficult |

**Grade labels:**

| Grade | Label |
| --- | --- |
| 0–5 | Very Easy (5th grade) |
| 6–8 | Easy (6th–8th grade) |
| 9–12 | Standard (9th–12th grade) |
| 13–16 | Difficult (college level) |
| 17+ | Very Difficult (graduate level) |

**Comparison mode:**

```bash
cd-agency score readability -i "Submit" -c "Click here to submit your information"
```

```
--- Before/After Comparison ---
  Grade level: 6.4 -> 8.4 (+2.0)
  Reading ease: 59.7 -> 36.6 (-23.1)
  Word count: 6 -> 1 (-5)
```

---

## `score lint`

Run content lint rules on text.

```bash
cd-agency score lint [OPTIONS]
```

**Options:**

| Option | Short | Type | Description |
| --- | --- | --- | --- |
| `--input` | `-i` | string | Text to lint |
| `--file` | `-f` | path | Read from file |
| `--type` | `-t` | choice | Content type (see below) |
| `--json-output` | | flag | Output as JSON |

**Content types:**

| Type | Rules Applied |
| --- | --- |
| `general` | Jargon, inclusive language, passive voice |
| `cta` | + CTA action verb, button character limit |
| `button` | + CTA action verb, button character limit |
| `error` | + Error actionable language |
| `notification` | + Notification character limit (120 chars) |
| `microcopy` | + Additional passive voice check |

**Lint rules:**

| Rule | Severity | Description |
| --- | --- | --- |
| `no-jargon` | warning | Flags buzzwords and corporate jargon |
| `inclusive-language` | error | Flags exclusionary terms (e.g., "whitelist" → "allowlist") |
| `no-passive-voice` | warning | Detects passive voice patterns |
| `cta-action-verb` | error | CTA must start with an action verb |
| `button-char-limit` | error | Button text must be ≤ 40 characters |
| `notification-char-limit` | error | Notification text must be ≤ 120 characters |
| `error-actionable` | error | Error messages must include resolution guidance |
| `consistent-terminology` | warning | Detects mixed terminology (e.g., "log in" + "login") |

**Example:**

```bash
cd-agency score lint -i "Click here to learn more!" --type button
```

```
[FAIL] cta-action-verb: CTA should start with an action verb, found 'click'
       -> Try starting with: claim, discover, explore, invite, learn, log, submit, take...
[PASS] button-char-limit: Button text is 25 chars (limit: 40)
```

---

## `score a11y`

Check text for WCAG text-level accessibility issues.

```bash
cd-agency score a11y [OPTIONS]
```

**Options:**

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--input` | `-i` | string | | Text to check |
| `--file` | `-f` | path | | Read from file |
| `--target-grade` | | float | `8.0` | Target reading grade level |
| `--json-output` | | flag | | Output as JSON |

**Accessibility checks:**

| Rule | Severity | WCAG | Description |
| --- | --- | --- | --- |
| `reading-level` | high | 3.1.5 | Grade level exceeds target |
| `sentence-length` | medium | 3.1.5 | Sentences over 25 words |
| `no-all-caps` | medium | 1.3.1 | ALL CAPS text (not abbreviations) |
| `emoji-overuse` | medium | 1.1.1 | Too many emoji (3 per 100 words max) |
| `descriptive-link-text` | high | 2.4.4 | "Click here" anti-patterns |
| `image-alt-text` | critical | 1.1.1 | Images without alt text |
| `meaningful-alt-text` | high | 1.1.1 | Filename used as alt text |

**Severity levels:**

| Level | Effect on Overall Pass |
| --- | --- |
| `critical` | Causes failure |
| `high` | Causes failure |
| `medium` | Warning only |
| `low` | Informational |

---

## `score voice`

Check text against a brand voice guide. Requires a voice profile YAML file.

```bash
cd-agency score voice [OPTIONS]
```

**Options:**

| Option | Short | Type | Description |
| --- | --- | --- | --- |
| `--input` | `-i` | string | Text to check |
| `--file` | `-f` | path | Read from file |
| `--guide` | `-g` | path | Brand voice YAML file **(required)** |
| `--no-llm` | | flag | Use rule-based check (no API call) |
| `--json-output` | | flag | Output as JSON |

**Example:**

```bash
cd-agency score voice -i "Click here to see details" \
  --guide presets/material-design.yaml --no-llm
```

**Score scale:**

| Score | Label |
| --- | --- |
| 9–10 | Excellent |
| 7–8 | Good |
| 5–6 | Needs Work |
| 3–4 | Poor |
| 1–2 | Off-Brand |

---

## `score all`

Run all scoring tools at once (readability + lint + a11y).

```bash
cd-agency score all [OPTIONS]
```

**Options:**

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--input` | `-i` | string | | Text to score |
| `--file` | `-f` | path | | Read from file |
| `--type` | `-t` | choice | `general` | Content type for lint rules |
| `--json-output` | | flag | | Output as JSON |
| `--markdown` | | flag | | Output as Markdown |

**Example:**

```bash
cd-agency score all -i "Your changes have been saved successfully." --json-output
```

The overall pass/fail is determined by:

- Any lint errors → **FAIL**
- Any critical or high a11y issues → **FAIL**
- Voice score < 5 → **FAIL** (when voice is included)
- Otherwise → **PASS**
