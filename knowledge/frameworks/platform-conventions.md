---
title: "Platform-Specific Content Conventions"
domain: frameworks
tags: [ios, android, web, mobile, desktop, platform, conventions, material-design, hig]
relevance: all
---

## Platform-Specific Content Rules

The same message needs different treatment on iOS, Android, web, and desktop. These aren't preferences — they're platform conventions that users expect.

### iOS (Apple Human Interface Guidelines)

**Capitalization:**
- **Title Case** for buttons, navigation, tab bars, alerts: "Sign In," "Manage Subscription"
- **Sentence case** for descriptions and body text
- Alert button order: **destructive action on the LEFT**, cancel on the RIGHT (opposite of Android)

**Terminology (Apple-specific):**
- "Settings" (not "Preferences")
- "Touch ID" / "Face ID" (proper nouns, always capitalized)
- "App" (not "application")
- "Tap" (not "click" or "press")
- "Swipe" (not "slide")
- "Home Screen" (capitalized)

**Alert Dialogs:**
- Title: short, specific question or statement (Title Case)
- Body: optional, only if the title isn't self-explanatory
- Buttons: 2 max preferred, 3 if essential
- Destructive actions use red text
- Example: Title "Delete This Photo?" / Body: "This action can't be undone." / Buttons: "Delete" (red) | "Cancel"

**Push Notifications:**
- Title: ≤ 50 chars (app name often auto-prepended)
- Body: ≤ 120 chars for full lock screen display
- Rich notifications support images and action buttons
- Avoid repeating the app name in the notification title

**Tone:**
- Apple prefers: clean, direct, minimal
- Avoid: exclamation marks, ALL CAPS, emoji in system-level UI
- OK to use: warmth in onboarding, personality in empty states

### Android (Material Design 3)

**Capitalization:**
- **Sentence case** for almost everything: buttons, titles, labels
- Exception: acronyms (GPS, URL) stay uppercase
- "Sign in" not "Sign In" — this is the biggest difference from iOS

**Terminology (Android/Google-specific):**
- "Settings" (same as iOS)
- "Tap" for touch, "Click" only for mouse/trackpad
- "Notifications" (not "alerts")
- "Floating action button" (FAB) — the round + button
- "Bottom sheet" (the pull-up panel)
- "Snackbar" (not "toast" — though similar; snackbars can have actions, toasts can't)

**Snackbars (Android-specific):**
- Single line: ≤ 60 chars
- Two lines max: ≤ 120 chars
- Optional action button: ≤ 10 chars (e.g., "UNDO," "RETRY")
- Auto-dismiss after 4-10 seconds
- Text: sentence case, no period for single sentences

**Dialogs:**
- Title: sentence case, concise
- Body: 1-3 sentences
- Button order: **cancel on the LEFT**, confirm on the RIGHT (opposite of iOS!)
- Use text buttons, not filled buttons, in dialogs
- Destructive actions: use "Delete" not "OK" (be specific)

**Notifications:**
- Title: ≤ 40 chars (app name shown separately)
- Body: ≤ 90 chars for collapsed view
- Expanded view supports longer text + images
- Action buttons: ≤ 3, text ≤ 12 chars each

**Tone:**
- Material Design prefers: friendly, accessible, sentence case
- Avoid: overly formal language, jargon
- OK to use: conversational tone, light personality

### Web (General Best Practices)

**Capitalization:**
- Varies by brand — follow the style guide
- Common pattern: Sentence case for most UI, Title Case for page titles
- Navigation: usually sentence case on modern sites

**Terminology:**
- "Click" (for mouse), "Tap" (for touch), or "Select" (device-agnostic)
- "Link" (not "hyperlink")
- "Page" (not "screen" — on web, it's a page)
- "Sign in" / "Log in" — pick one and be consistent
- "Email" (not "e-mail" — the hyphen is dead)

**Buttons:**
- Primary button: filled, prominent, single primary per screen
- Secondary button: outlined or text-only
- Destructive button: red or separate confirmation step
- Button text: verb-first ("Create account," "Download report")
- Avoid: "Submit," "OK," "Click here" — be specific

**Forms:**
- Labels above fields (not beside — breaks on mobile)
- Required fields: mark with asterisk (*) AND state "Required" for screen readers
- Placeholder text: light hint, NEVER the only label (disappears on focus)
- Error messages: appear below the field, in red, with specific fix instruction
- Success states: brief confirmation, auto-dismiss if possible

**Modals:**
- Headline: clear question or statement
- Body: ≤ 3 sentences
- Always include a close mechanism (X button, click outside, Escape key)
- Focus trap: keyboard focus stays inside the modal
- Screen readers: announce modal title on open

### Cross-Platform Consistency

When designing for multiple platforms, follow these rules:

**Keep consistent:**
- Brand voice and tone
- Terminology for product-specific concepts ("workspace," "project," "team")
- Core messaging and value propositions
- Error message content (the WHAT went wrong)

**Adapt per platform:**
- Capitalization (Title Case on iOS, sentence case on Android)
- Button order (iOS: destructive left, Android: confirm right)
- Character limits (vary by element and platform)
- Interaction verbs ("tap" on mobile, "click" on desktop, "select" for device-agnostic)
- Alert/dialog structure

### Quick Reference: Platform Differences

| Element | iOS | Android | Web |
|---------|-----|---------|-----|
| Button case | Title Case | sentence case | Varies (style guide) |
| Confirm button position | Right | Right | Right |
| Cancel button position | Left | Left | Left |
| Destructive action | Red text, left | Red text or separate dialog | Red button or confirm step |
| Interaction verb | "Tap" | "Tap" | "Click" or "Select" |
| Toast/Snackbar max | ~50 chars | 60 chars (single line) | 60-80 chars |
| Push title max | 50 chars | 40 chars | N/A (browser: ~50 chars) |
| Push body max | 120 chars | 90 chars (collapsed) | 120 chars (browser) |
| Settings term | "Settings" | "Settings" | "Settings" or "Preferences" |

### When Platform Conventions Conflict with Brand

If your brand guide says "Use Title Case everywhere" but Android conventions say "sentence case":

1. **Platform conventions win for system-level UI** (alerts, settings, notifications)
2. **Brand voice wins for marketing content** (landing pages, onboarding, in-app promos)
3. **When in doubt, follow the platform** — users have muscle memory for their OS patterns
4. **Document exceptions explicitly** — "We use sentence case on Android per Material Design guidelines, even though our brand guide specifies Title Case"
