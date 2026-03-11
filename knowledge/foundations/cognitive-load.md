---
title: Cognitive Load Theory for Content Design
domain: foundations
tags: [psychology, cognitive-load, ux, decision-making]
sources:
  - "Sweller, J. (1988). Cognitive Load During Problem Solving"
  - "Miller, G. (1956). The Magical Number Seven, Plus or Minus Two"
  - "Hick, W.E. (1952). On the Rate of Gain of Information"
  - "Don't Make Me Think — Steve Krug"
---

### Core Principle

Every word on screen competes for the user's limited working memory. Content designers are cognitive load managers — our job is to reduce the mental effort required to understand and act.

### Three Types of Cognitive Load

1. **Intrinsic load** — the inherent complexity of the task itself. You can't eliminate it, but you can sequence it (progressive disclosure) and chunk it into manageable pieces.

2. **Extraneous load** — unnecessary complexity added by poor design or writing. This is what content designers must eliminate. Jargon, ambiguity, walls of text, redundant words — all extraneous load.

3. **Germane load** — the productive mental effort of learning and building understanding. Good content supports this by using consistent patterns, familiar metaphors, and clear mental models.

### Miller's Law: 7 ± 2

Working memory holds roughly 5-9 items. Implications for content:
- **Navigation menus:** 5-7 items maximum
- **Form fields per screen:** 5-7 visible at once
- **Steps in a process:** 3-5 steps before showing progress
- **Options in a list:** Group into categories if more than 7
- **Key points in a message:** 3 is ideal, 5 is maximum

### Hick's Law: Choice Overload

Decision time increases logarithmically with the number of options. For content:
- **Reduce choices.** One primary CTA per screen.
- **Create clear defaults.** Pre-select the most common option.
- **Use progressive disclosure.** Show only what's needed now.
- **Label options clearly.** Ambiguous labels force users to think harder about each choice.

### Cognitive Load Reduction Techniques

**Chunking:** Break content into scannable groups with clear headers.
```
Bad:  "Enter your first name, last name, email address, phone number, and shipping address to complete your order."
Good: [First name] [Last name]
      [Email]
      [Phone]
      [Shipping address]
```

**Familiar patterns:** Use conventions users already know.
- "Sign in" not "Authenticate"
- "Search" not "Query"
- Red for errors, green for success

**Consistency:** Same action = same words everywhere.
- If "Delete" is used on one screen, don't use "Remove" on another for the same action (unless semantically different).

**Scannability:** Users scan in F-patterns. Put key info at the start of each line.
```
Bad:  "To undo this action, click the Undo button"
Good: "Undo — click to reverse this action"
```

### The "Moment of Maximum Cognitive Load"

Identify when users are under the most mental stress — errors, payments, data loss warnings, complex forms — and make content simplest at those moments. This is counterintuitive: the most critical moments get the fewest, clearest words.

### Word Budget

Every screen has an invisible word budget. Exceeding it means users skip content entirely. Guidelines:
- **Error messages:** 10-20 words
- **Tooltips:** 5-15 words
- **Button labels:** 1-3 words
- **Empty states:** 15-30 words
- **Onboarding steps:** 20-40 words per step
- **Notifications:** 10-25 words
