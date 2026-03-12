---
title: Readability Science and Formulas
domain: frameworks
tags: [readability, scoring, measurement, plain-language]
sources:
  - "Flesch, R. (1948). A New Readability Yardstick"
  - "Kincaid, J.P. et al. (1975). Derivation of New Readability Formulas"
  - "Dale, E. & Chall, J. (1948). A Formula for Predicting Readability"
  - "DuBay, W. (2004). The Principles of Readability"
---

### Core Principle

Readability formulas estimate how easy text is to read based on measurable properties like word length, sentence length, and vocabulary. They are proxies — useful benchmarks but not substitutes for human judgment and user testing.

### Key Readability Formulas

**Flesch Reading Ease (FRE)**
```
FRE = 206.835 - 1.015 × (words/sentences) - 84.6 × (syllables/words)
```
Scale: 0-100 (higher = easier)
- 90-100: Very easy (5th grade)
- 80-89: Easy (6th grade)
- 70-79: Fairly easy (7th grade)
- 60-69: Standard (8th-9th grade) ← target for most UI
- 50-59: Fairly difficult (10th-12th grade)
- 30-49: Difficult (college level)
- 0-29: Very confusing (graduate level)

**Flesch-Kincaid Grade Level**
```
Grade = 0.39 × (words/sentences) + 11.8 × (syllables/words) - 15.59
```
Returns a US grade level. Target: 6-8 for consumer apps.

**SMOG Index**
```
SMOG = 3 + √(polysyllable count × 30 / sentence count)
```
More conservative — tends to rate text harder than Flesch-Kincaid.

**Dale-Chall Formula**
Uses a list of 3,000 "familiar words." Words not on the list are considered difficult. More vocabulary-focused than syllable-based formulas.

### What the Formulas Actually Measure

| Factor | What it captures | Limitation |
|--------|-----------------|------------|
| **Sentence length** | Complexity, working memory load | Short sentences can still be unclear |
| **Word length/syllables** | Vocabulary difficulty | "Interface" is simpler than "make do" in context |
| **Passive voice %** | Directness | Some passive voice is appropriate |
| **% of complex words** | Vocabulary accessibility | Technical terms may be necessary and known |

### Why Formulas Aren't Enough

Readability formulas cannot measure:
- **Context appropriateness** — "Delete" is a simple word but a complex action
- **Conceptual complexity** — "Your data is encrypted" is readable but may not be *understood*
- **Visual readability** — Font size, contrast, line length affect comprehension
- **Scannability** — Bullets vs. paragraphs aren't captured
- **Emotional clarity** — A message can be readable but still feel cold or confusing
- **Cultural sensitivity** — Idioms score as "easy" but fail for international audiences

### Practical Readability Targets

| Content type | FRE score | Grade level | Avg sentence length |
|-------------|-----------|-------------|-------------------|
| Button/CTA | 90+ | 3-5 | 1-5 words |
| Error message | 70-90 | 5-7 | 8-15 words |
| Tooltip | 70-90 | 5-7 | 5-12 words |
| Notification | 70-85 | 6-8 | 10-15 words |
| Onboarding | 65-80 | 6-8 | 10-18 words |
| Help article | 60-75 | 7-9 | 12-20 words |
| Legal/privacy | 50-65 | 8-10 | 15-20 words |

### Quick Readability Improvements

1. **Split long sentences.** If a sentence has a comma, try splitting it into two sentences.
2. **Replace long words.** "Utilize" → "use," "commence" → "start," "subsequently" → "then"
3. **Remove hedge words.** "Basically," "essentially," "actually," "really"
4. **Cut prepositional chains.** "The settings page of the admin section of your account" → "Account settings"
5. **Use verbs, not nouns.** "Make a selection" → "Select," "Perform a search" → "Search"

### Beyond the Score

A readability score is a starting point, not a grade. Always combine with:
- Reading the text aloud
- Testing with real users
- Checking comprehension, not just reading speed
- Evaluating in context (on screen, at actual size)
