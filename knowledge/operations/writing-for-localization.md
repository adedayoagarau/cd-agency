---
title: Writing Content That Localizes Well
domain: operations
tags: [localization, i18n, translation, global, internationalization, l10n]
sources:
  - "W3C. Internationalization Best Practices"
  - "Mozilla. Localization Best Practices"
  - "Shopify. Polaris Internationalization Guidelines"
---

### Core Principle

Writing for localization means writing source content (usually English) that translates cleanly into any language. It's not about translation — it's about writing the original content so well that translation becomes straightforward.

### The Localization-Ready Writing Rules

**1. Use simple, standard sentence structure.**
- Subject-verb-object order
- One idea per sentence
- Avoid complex nested clauses
- Bad: "The file you uploaded, which exceeded the size limit we mentioned in the tooltip, couldn't be saved."
- Good: "Your file is too large. The maximum size is 10 MB."

**2. Avoid idioms, slang, and cultural references.**
- "Ballpark figure" → "approximate number"
- "Touch base" → "check in" or "follow up"
- "Low-hanging fruit" → "easy wins" or "quick improvements"
- Sports metaphors, holiday references, pop culture — all fail internationally

**3. Don't concatenate strings.**
```
Bad (in code):  "You have " + count + " items in your " + container
Problem: Word order changes in other languages. German might need: "In Ihrem Warenkorb befinden sich 3 Artikel"
Good: "You have {count} items in your {container}"
Use full sentence templates with placeholders.
```

**4. Handle plurals properly.**
```
Bad:  "You have " + count + " item(s)"
Problem: Many languages have 3+ plural forms (one, few, many)
Good: Use ICU MessageFormat:
  "{count, plural, =0 {No items} =1 {1 item} other {{count} items}}"
```

**5. Don't embed text in images.**
- Text in images can't be translated without recreating the image
- Use text overlays or SVGs with translatable strings instead

**6. Design for text expansion.**
- German: ~30% longer than English
- Finnish: ~30-40% longer
- Japanese: Often shorter (but vertical space may increase)
- Arabic/Hebrew: Right-to-left (entire layout may mirror)
- Rule: Design UI with 50% extra space for text

### String Writing Best Practices

**Write complete, self-contained strings:**
```
Bad:  "by" (used as "Created by Sarah" — but "by" alone is untranslatable)
Good: "Created by {author_name}"
```

**Include context for translators:**
```
String: "Save"
Context: "Button label — saves the current document to the user's account"
Without context, "save" could be translated as rescue, economize, or preserve.
```

**Avoid reusing strings across contexts:**
```
"Cancel" on a form (abandon the form) ≠ "Cancel" on a subscription (end the subscription)
These may need different translations in some languages.
```

### Date, Time, and Number Formatting

| Format | US English | German | Japanese |
|--------|-----------|--------|----------|
| Date | March 15, 2024 | 15. März 2024 | 2024年3月15日 |
| Short date | 3/15/2024 | 15.03.2024 | 2024/03/15 |
| Time | 2:30 PM | 14:30 | 14:30 |
| Number | 1,234.56 | 1.234,56 | 1,234.56 |
| Currency | $1,234.56 | 1.234,56 € | ¥1,234 |

**Rules:**
- Never hardcode date/number formats — use locale-aware formatters
- Store dates in ISO 8601 (YYYY-MM-DD) and display in local format
- Show relative time when possible: "5 minutes ago" (localization libraries handle this)

### Layout and RTL Considerations

**Right-to-left (Arabic, Hebrew):**
- Text alignment flips from left to right
- Icons that imply direction (arrows, progress bars) must be mirrored
- "Back" button moves to the right side
- Exception: phone numbers, code, and LTR-embedded text stay LTR
- Progress bars may or may not flip (context-dependent)

**Character sets:**
- Chinese/Japanese/Korean (CJK): May need larger font sizes for readability
- Arabic: Connected script — letter forms change based on position
- Thai/Khmer: No spaces between words — line-breaking rules differ

### Localization Testing Checklist

1. **Pseudo-localization:** Replace text with accented characters (àccéntéd) to catch hardcoded strings
2. **Text expansion test:** Artificially lengthen all strings by 50% — does the UI still work?
3. **RTL test:** Mirror the entire UI — does layout hold?
4. **Date/number test:** Switch locale — do formats update correctly?
5. **Plural test:** Test with 0, 1, 2, 5, 21 items — do all plural forms work?
6. **Truncation test:** What happens when translated text is longer than the container?
