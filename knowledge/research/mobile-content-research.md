---
title: Mobile-First Content Design Research
domain: research
tags: [mobile, responsive, touch, thumb-zone, small-screen, app]
sources:
  - "Hoober, S. (2017). Design for Fingers, Touch, and People"
  - "Wroblewski, L. (2011). Mobile First"
  - "Google/SOASTA (2017). Mobile Page Speed Study"
  - "Nielsen Norman Group. Mobile UX Research"
---

### Core Findings

**Users aren't "on the go":** 68% of mobile usage happens at home (Google research). Mobile users want the same content as desktop users — they're just on a smaller screen.

**Attention is fragmented:** Mobile sessions average 72 seconds. Users are interrupted, multitasking, and switching apps. Content must communicate value in the first few seconds.

**Every word costs more on mobile:** Smaller screen = fewer visible words = higher cost per word. The bar for inclusion is higher: if a word doesn't help, it actively hurts on mobile.

### Screen Real Estate Rules

**Above the fold matters more on mobile:**
- First screen = 300-400 words maximum (depends on font size)
- Primary headline + CTA must be visible without scrolling
- No "Welcome to..." preamble — start with value

**Touch targets need text:**
- Minimum touch target: 48x48px (Apple says 44x44pt)
- Button text must be readable at that size
- Icon-only buttons need labels (accessibility + clarity)

**Thumb zone awareness:**
- Easy reach: bottom center and middle of screen
- Hard reach: top corners
- Primary CTAs should be in the easy-reach zone
- "Back" and navigation: top (convention, despite being harder to reach)

### Mobile Content Patterns

**Push notifications:**
```
Title: 40-50 characters (truncated after ~50)
Body: 80-120 characters (varies by OS)
Must communicate value without opening the app
Example: "Your order shipped — arriving Thursday"
```

**In-app messages:**
```
Short headline: 3-7 words
Body: 1-2 sentences maximum
One clear CTA button
Always dismissible
Example: "New: Dark mode is here" + [Try it] / [✕]
```

**Mobile forms:**
- One field visible per screen (GOV.UK pattern) for complex forms
- Input type must match keyboard: email → email keyboard, phone → number pad
- Autocomplete enabled for standard fields
- Large, clear submit buttons (full-width on mobile)

**Mobile error messages:**
- Must be visible without scrolling to the field
- Consider a summary at the top: "2 fields need attention"
- Inline errors near each field
- Don't clear the user's input on error

### Character Limits by Component (Mobile)

| Component | Max chars | Example |
|-----------|----------|---------|
| Button | 20-25 | "Save changes" |
| Tab label | 10-15 | "Activity" |
| Push title | 40-50 | "New message from Sarah" |
| Push body | 80-120 | "Hey, are you free for lunch tomorrow?" |
| Toast/snackbar | 40-60 | "Message sent" / "Changes saved" |
| Alert title | 30-40 | "Delete this photo?" |
| Alert body | 80-120 | "This photo will be permanently deleted." |
| Bottom sheet title | 25-35 | "Sort by" |
| Badge | 1-3 | "99+" |

### Mobile vs. Desktop Content Adaptation

| Desktop | Mobile adaptation |
|---------|------------------|
| "Click here to learn more" | "Learn more" (no "click" — it's "tap") |
| Full product descriptions | Scannable bullets, expandable details |
| Side-by-side comparison tables | Stacked cards or swipeable comparison |
| Multi-column layouts | Single column, progressive disclosure |
| Hover tooltips | Tap-to-reveal or inline help text |
| "Right-click to save" | "Tap and hold to save" |

### Performance and Content

**Google research findings:**
- 53% of mobile users abandon sites that take over 3 seconds to load
- Every additional second of load time = 20% drop in conversions
- Content that loads progressively (skeleton screens) feels faster

**Implications for content:**
- Prioritize above-the-fold content in loading order
- Use progressive disclosure aggressively
- Lazy-load images and non-critical content
- Keep page weight minimal — every font, image, and script competes with content

### Mobile-Specific Accessibility

- **Font size:** Minimum 16px body text (prevents zoom on iOS)
- **Line length:** 40-60 characters per line on mobile
- **Contrast:** Even more critical on mobile (sunlight, glare)
- **Touch targets:** 48px minimum, with 8px spacing between
- **Reduce cognitive load:** Fewer choices, clearer hierarchy, shorter text
- **Orientation:** Content must work in both portrait and landscape
