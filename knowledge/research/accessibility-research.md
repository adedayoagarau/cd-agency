---
title: Accessibility Research for Content Design
domain: research
tags: [accessibility, wcag, inclusive-design, screen-readers, cognitive]
sources:
  - "W3C Web Content Accessibility Guidelines (WCAG) 2.1 & 2.2"
  - "W3C Cognitive Accessibility Guidance (COGA)"
  - "WebAIM Screen Reader User Survey"
  - "Deque University. Accessibility Research & Guidelines"
---

### Why Content Accessibility Matters

- 1.3 billion people worldwide experience significant disability (WHO)
- 15-20% of the population has a learning disability like dyslexia
- Accessible content benefits everyone — situational impairment (bright sunlight, noisy room) affects all users at some point
- Accessible content is better content — the techniques that help disabled users also help everyone

### WCAG Content Requirements

**Perceivable:**
- **1.1.1 Non-text Content:** All images need meaningful alt text. Decorative images get `alt=""`
- **1.3.1 Info and Relationships:** Headings must use proper heading elements (not just bold text). Lists must use list elements.
- **1.4.5 Images of Text:** Don't use images of text — use real text

**Operable:**
- **2.4.2 Page Titled:** Every page needs a unique, descriptive title
- **2.4.4 Link Purpose:** Link text must make sense out of context. "Click here" and "Learn more" fail this. "Read our privacy policy" passes.
- **2.4.6 Headings and Labels:** Headings and labels must describe the topic or purpose

**Understandable:**
- **3.1.1 Language of Page:** Specify the document language
- **3.1.2 Language of Parts:** Mark up content in a different language
- **3.2.2 On Input:** Don't change context unexpectedly when users interact with form fields
- **3.3.1 Error Identification:** Identify the item in error and describe the error in text
- **3.3.2 Labels or Instructions:** Provide labels or instructions for user input
- **3.3.3 Error Suggestion:** If an error is detected and suggestions are known, provide them

### Writing for Screen Readers

**Alt text best practices:**
- Describe the function, not the appearance: "Submit button" not "blue button"
- For informational images: describe the content: "Bar chart showing 40% increase in Q3"
- For decorative images: use empty alt text (`alt=""`)
- Keep alt text under 125 characters
- Don't start with "Image of" or "Picture of" — the screen reader already announces it's an image

**Link text:**
- Unique and descriptive out of context
- Bad: "Click here" / "Read more" / "Learn more"
- Good: "Download the annual report (PDF, 2.4 MB)" / "View your order history"
- Screen reader users often navigate by links — every "click here" sounds identical

**Heading hierarchy:**
- Use proper heading levels (h1 → h2 → h3) — don't skip levels
- Screen reader users navigate by headings — they function as a table of contents
- Every heading should make sense on its own, out of context

**Form labels:**
- Every form field needs a visible, associated label
- Placeholder text is NOT a label — it disappears on focus
- Group related fields with fieldset and legend
- Error messages must be associated with the field they describe

### Cognitive Accessibility (COGA)

The W3C's Cognitive Accessibility Guidance addresses users with:
- Learning disabilities (dyslexia, dyscalculia)
- Cognitive disabilities (intellectual disabilities, attention deficit)
- Age-related cognitive decline
- Temporary cognitive impairment (stress, fatigue, medication)

**Key content principles from COGA:**

1. **Use literal language.** Avoid metaphors, idioms, and sarcasm that may not be universally understood. "Start" not "Hit the ground running."

2. **Be predictable.** Consistent terminology, consistent placement, consistent behavior. Surprises are enemies of cognitive accessibility.

3. **Support recognition over recall.** Labels on buttons, clear navigation, visible instructions.

4. **Provide enough time.** Don't auto-dismiss notifications too quickly. Don't timeout forms during completion.

5. **Minimize required reading.** Every word is a barrier for users with reading difficulties. Ruthlessly cut unnecessary content.

6. **Use clear, simple language.** Short sentences, common words, one instruction per step.

7. **Support multiple input methods.** Don't rely on hover for essential information (tooltips with critical content).

### Inclusive Language

- **Gender:** Use "they/them" for unknown gender. Avoid "he or she."
- **Disability:** "Person with a disability" not "disabled person" (person-first). But respect community preferences — many Deaf people prefer "Deaf person" (identity-first).
- **Age:** Avoid ageist language. "Older adults" not "the elderly."
- **Technical ability:** Don't use "easy" or "simple" — what's easy for you may not be easy for everyone.
- **Culture:** Avoid idioms that don't translate. "Ballpark figure," "touch base," and "low-hanging fruit" are meaningless to non-native English speakers.

### Testing Content for Accessibility

1. **Screen reader test:** Have content read aloud. Does it make sense linearly?
2. **Heading navigation test:** Read only the headings. Can you understand the page structure?
3. **Link list test:** List all links. Does each one make sense without surrounding context?
4. **Zoom test:** At 200% zoom, is all content still readable and functional?
5. **Plain language test:** Can a user with low literacy understand the core message and required action?
