---
title: "UI Constraints Reference for Content Designers"
domain: frameworks
tags: [constraints, character-limits, screen-size, buttons, forms, mobile, desktop, platform]
relevance: all
---

## UI Constraints Every Content Designer Must Know

Content doesn't exist in a vacuum. It lives inside buttons, modals, tooltips, notifications, and screens — each with hard limits. Ignoring constraints produces content that truncates, wraps awkwardly, or breaks layouts.

### Character Limits by Element

These are practical maximums, not theoretical ideals. Design for these.

| UI Element | Max Characters | Notes |
|-----------|---------------|-------|
| **Button (primary)** | 20-25 chars | 1-3 words. Must be scannable at a glance. |
| **Button (secondary)** | 30 chars | Can be slightly longer but still single-line. |
| **Navigation label** | 15-20 chars | Must fit in nav bar/tab bar without truncation. |
| **Tab label** | 12-18 chars | Shorter is always better for tabs. |
| **Tooltip** | 80-120 chars | 1-2 sentences max. Must be self-contained. |
| **Toast/snackbar** | 40-60 chars | Visible for ~4 seconds. Must be instant to parse. |
| **Push notification (title)** | 40-50 chars | Truncates on lock screen after this. |
| **Push notification (body)** | 100-120 chars | iOS shows ~4 lines, Android ~1 line on lock screen. |
| **Email subject line** | 40-50 chars | Mobile email clients truncate at ~35-40 chars. |
| **Email preview text** | 80-100 chars | Shows after subject in inbox list. |
| **Form field label** | 25-40 chars | Must be above the field, not beside it on mobile. |
| **Placeholder text** | 30-45 chars | Disappears on focus — never use for critical info. |
| **Inline validation error** | 50-80 chars | Must explain AND guide without wrapping more than 2 lines. |
| **Modal headline** | 40-60 chars | Short, clear, action-oriented. |
| **Modal body** | 150-250 chars | 2-3 sentences maximum. People don't read modals. |
| **Empty state headline** | 30-50 chars | Empathetic and clear. |
| **Empty state body** | 80-150 chars | Explain what to do next. |
| **Breadcrumb segment** | 15-25 chars | Truncate with ellipsis if longer. |
| **Badge/tag** | 10-20 chars | Single word or short phrase. |
| **Banner message** | 80-150 chars | Dismissible; must include CTA if action is needed. |

### Screen Size Constraints

Content behaves differently across devices:

**Mobile (320-428px width)**
- Usable text area: ~280-380px after padding
- Users hold phone with one hand, tap with thumb
- Scanning speed: ~3-5 words per glance
- Reading context: distracted, bright sunlight, walking, multitasking
- Content strategy: ruthlessly short, front-load key info, one action per screen
- Buttons: full-width is common; text must be very short

**Tablet (768-1024px width)**
- Hybrid context: sometimes lean-back (reading), sometimes lean-forward (working)
- More space but don't fill it — white space aids comprehension
- Can support side-by-side layouts, which changes content hierarchy

**Desktop (1024px+ width)**
- Users are typically focused, sitting at a desk
- Can handle longer content, but still scan first
- Multi-column layouts mean content competes for attention
- Hover states available — tooltips work here but not on mobile

### Space Budgets

Think of content in terms of space budgets:

**Tight budget (≤ 25 chars):** Buttons, labels, tabs, badges
- Every character matters
- Use verbs: "Save," "Send," "Create project"
- No articles ("the," "a"), no filler words

**Medium budget (25-80 chars):** Tooltips, toasts, inline errors, short descriptions
- One complete thought
- Subject + verb + object: "Your password needs at least 8 characters"
- No compound sentences

**Generous budget (80-250 chars):** Modal bodies, empty states, banners, notification bodies
- 2-3 sentences
- Can include context + action
- Still prioritize scannability

**Expansive (250+ chars):** Help articles, onboarding screens, email bodies
- Use headings, bullets, short paragraphs
- Progressive disclosure: lead with the essential, details below
- Chunk into scannable sections

### Localization Expansion Factors

If content will be translated, budget for expansion:

| Target Language | Expansion Factor | Example |
|----------------|-----------------|---------|
| German | +30-35% | "Save changes" → "Änderungen speichern" |
| French | +15-20% | "Save changes" → "Enregistrer les modifications" |
| Spanish | +20-25% | "Save changes" → "Guardar cambios" |
| Italian | +15-20% | "Save changes" → "Salva le modifiche" |
| Portuguese | +20-30% | "Save changes" → "Salvar alterações" |
| Japanese | -10-20% (chars) | Characters are wider, but text is often shorter |
| Arabic/Hebrew | Similar length | RTL layout requires different design considerations |
| Chinese | -30-50% (chars) | Characters are wider; layout implications differ |

**Rule of thumb:** If your English button text is 20 characters, budget for 26-27 characters to accommodate German translation.

### Typography Constraints

- **Minimum readable font size:** 16px on mobile, 14px on desktop (WCAG)
- **Line length:** 50-75 characters per line for readability (measure in ch units)
- **Line height:** 1.4-1.6 for body text, 1.2-1.3 for headings
- **All-caps text:** Harder to read; limit to labels and very short text (≤ 3 words)
- **Truncation with ellipsis:** Only acceptable for non-essential info; never truncate CTAs or error messages

### Touch Target Constraints

- **Minimum touch target:** 44×44px (iOS), 48×48dp (Android Material)
- **Spacing between targets:** ≥ 8px to prevent mis-taps
- **Implications for text:** Button text must be short enough to fit within the minimum target width with padding
- **Thumb zone:** Primary actions should be in the bottom 40% of mobile screens

### Constraint-First Thinking

When given a content request, ask these constraint questions in order:

1. **What element is this?** (button, tooltip, modal, notification, etc.)
2. **What platform?** (mobile, desktop, both, native app, web)
3. **What's the character budget?** (use the table above as defaults)
4. **Will it be translated?** (multiply by expansion factor)
5. **What's the visual hierarchy?** (primary action, secondary, tertiary)
6. **What's near it?** (other text, images, whitespace — affects how much context you need)
7. **How long will the user see it?** (toast = 4 seconds, modal = until dismissed, push = glance)
