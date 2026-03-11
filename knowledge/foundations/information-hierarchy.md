---
title: Information Hierarchy in Content Design
domain: foundations
tags: [information-architecture, scannability, structure, layout]
sources:
  - "Redish, J. (2012). Letting Go of the Words"
  - "Nielsen, J. (2006). F-Shaped Pattern of Reading on the Web (NNG)"
  - "Krug, S. (2014). Don't Make Me Think, Revisited"
---

### Core Principle

Users don't read — they scan. Content hierarchy determines what gets seen first, what gets skipped, and what drives action. Every piece of content needs a visual and semantic priority order.

### The F-Pattern

Eye-tracking research by Nielsen Norman Group shows users scan web content in an F-pattern:
1. **First horizontal sweep** across the top (headline, nav)
2. **Second horizontal sweep** slightly lower (subhead, first paragraph)
3. **Vertical scan** down the left side (first words of each line, bullets, bold text)

**Implication:** The first 2-3 words of every heading, label, and paragraph carry disproportionate weight. Front-load meaning.

### The Inverted Pyramid

Borrowed from journalism — put the most important information first:
1. **Lead:** The essential message or action (who, what, why)
2. **Body:** Supporting details and context
3. **Background:** Nice-to-have information

Applied to UI content:
```
Lead:       "Your subscription renews on March 15"
Body:       "You'll be charged $9.99/month to your Visa ending in 4242."
Background: "Manage your plan in Settings → Billing."
```

### Hierarchy Signals in UI Text

| Signal | Example | Effect |
|--------|---------|--------|
| **Headings** | "Payment failed" | Anchors attention, sets context |
| **Bold text** | "This action **cannot be undone**" | Draws eye to critical info |
| **Numbered lists** | "1. Choose a plan 2. Enter payment" | Implies sequence |
| **Bullet lists** | "• Free • No credit card • Cancel anytime" | Scannable features |
| **Short paragraphs** | 1-2 sentences max | Prevents text walls |
| **Whitespace** | Breathing room between sections | Groups related content |

### Content Hierarchy per UI Element

**Modals/Dialogs:**
1. Title (what's happening)
2. Body (context/consequences)
3. Primary action (what to do)
4. Secondary action (escape hatch)

**Cards:**
1. Title/label (what is this)
2. Key metric or status
3. Supporting detail
4. Action

**Notifications:**
1. What happened (title)
2. Why it matters (body)
3. What to do (action)

**Empty states:**
1. What goes here (explanation)
2. Why it's empty (context)
3. How to fill it (action)

### The Squint Test

Squint at your screen until you can't read the words. What stands out? That's your hierarchy. If the most important element doesn't stand out, adjust. The content hierarchy should work even when users can barely see the page — because that's how fast they scan.

### Common Hierarchy Mistakes

- **Burying the lede:** Putting context before the key message
- **Equal weight everywhere:** When everything is bold, nothing is bold
- **Orphaned actions:** CTAs disconnected from the content that motivates them
- **Wall of text:** Paragraphs longer than 3 lines on screen
- **Competing hierarchies:** Multiple elements fighting for primary attention
