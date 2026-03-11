# `tools.scoring` — Readability Scorer

> Stability: Stable

```python
from tools.scoring import ReadabilityScorer, ReadabilityResult
```

Calculates readability metrics for text content. No API key required.

## Class: `ReadabilityResult`

Results from readability analysis.

```python
@dataclass
class ReadabilityResult:
    text: str
    word_count: int
    character_count: int
    sentence_count: int
    syllable_count: int
    avg_sentence_length: float
    max_sentence_length: int
    min_sentence_length: int
    avg_word_length: float
    flesch_reading_ease: float      # 0–100 (higher = easier)
    flesch_kincaid_grade: float     # US grade level (lower = easier)
    complexity_index: float         # Ratio of 3+ syllable words
    reading_time_seconds: float     # At 238 WPM
```

### `result.grade_label`

Human-readable grade level label.

- Type: `str` (property)

| Grade | Label |
| --- | --- |
| 0–5 | Very Easy (5th grade) |
| 6–8 | Easy (6th–8th grade) |
| 9–12 | Standard (9th–12th grade) |
| 13–16 | Difficult (college level) |
| 17+ | Very Difficult (graduate level) |

### `result.ease_label`

Human-readable reading ease label.

- Type: `str` (property)

| Score | Label |
| --- | --- |
| 90–100 | Very Easy |
| 80–89 | Easy |
| 70–79 | Fairly Easy |
| 60–69 | Standard |
| 50–59 | Fairly Difficult |
| 30–49 | Difficult |
| 0–29 | Very Difficult |

### `result.to_dict()`

Convert to dictionary with all metrics.

- Returns: `dict`

---

## Class: `ReadabilityScorer`

### `scorer.score(text)`

Score text for readability metrics.

- `text`: `str`
- Returns: `ReadabilityResult`

```python
scorer = ReadabilityScorer()
result = scorer.score("Your changes have been saved.")

print(f"Words: {result.word_count}")
print(f"Grade: {result.flesch_kincaid_grade} ({result.grade_label})")
print(f"Ease: {result.flesch_reading_ease} ({result.ease_label})")
print(f"Complexity: {result.complexity_index}")
print(f"Reading time: {result.reading_time_seconds}s")
```

Empty text returns a zero-valued result.

### `scorer.compare(before, after)`

Compare readability of before and after text.

- `before`: `str`
- `after`: `str`
- Returns: `dict` with keys `"before"`, `"after"`, `"improvements"`.

```python
comparison = scorer.compare(
    "Click here to submit your information",
    "Submit",
)
print(comparison["improvements"])
# {"word_count_change": -5, "grade_change": 2.0, "ease_change": -23.1, ...}
```

### Formulas

**Flesch Reading Ease:**

```
206.835 − 1.015 × (words / sentences) − 84.6 × (syllables / words)
```

Clamped to 0–100.

**Flesch-Kincaid Grade:**

```
0.39 × (words / sentences) + 11.8 × (syllables / words) − 15.59
```

Minimum 0.

**Complexity Index:**

```
count(words with ≥ 3 syllables) / total words
```

**Reading Time:**

```
word_count / 238 × 60 seconds
```
