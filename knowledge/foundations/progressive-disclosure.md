---
title: Progressive Disclosure
domain: foundations
tags: [information-architecture, ux-patterns, complexity-management]
sources:
  - "Nielsen, J. (2006). Progressive Disclosure (NNG)"
  - "Tidwell, J. (2010). Designing Interfaces"
  - "Krug, S. (2014). Don't Make Me Think, Revisited"
---

### Core Principle

Show users only what they need at each moment. Defer advanced or secondary information until they ask for it or reach a stage where they need it. This reduces cognitive load without reducing capability.

### The Three Levels

1. **Primary:** What 80% of users need 80% of the time. Always visible.
2. **Secondary:** What power users or specific workflows need. One click/tap away.
3. **Tertiary:** Edge cases, advanced settings, detailed explanations. Two or more interactions away.

### Content Design Applications

**Onboarding:**
- Level 1: "Welcome to [App]. Let's set up your workspace." + single CTA
- Level 2: Customization options (theme, notifications) — shown after initial setup
- Level 3: Advanced integrations, API keys — available in settings

**Error messages:**
- Level 1: What happened + what to do ("Payment failed. Try again or use a different card.")
- Level 2: "Why did this happen?" expandable section
- Level 3: Error code, technical details for support

**Forms:**
- Level 1: Required fields only
- Level 2: Optional fields (revealed via "Add more details" or "Advanced options")
- Level 3: Help text on focus, tooltips on hover

**Settings:**
- Level 1: Most-changed settings (name, email, password)
- Level 2: Preferences (notifications, language, theme)
- Level 3: Developer options, data export, account deletion

### Writing Patterns for Progressive Disclosure

**The summary → detail pattern:**
```
[Short summary visible by default]
[Learn more →]  ← reveals full explanation
```

**The action → consequence pattern:**
```
Delete project                    ← primary action
This will permanently delete      ← revealed on click/hover
all files and cannot be undone.
```

**The status → detail pattern:**
```
3 issues found                    ← visible
[View details →]                  ← expands to show each issue
```

### Anti-Patterns

- **Information dumping:** Showing everything at once "just in case"
- **Mystery meat navigation:** Hiding primary content behind interactions
- **Over-nesting:** Requiring 4+ clicks to reach common features
- **Hidden required info:** Burying critical warnings in expandable sections
- **Tooltip dependency:** Requiring tooltips to understand the primary interface

### The 80/20 Rule in Practice

Audit any screen: what do 80% of users need? That's your primary layer. Everything else is progressive. If you're showing 20 options and analytics show 4 are used by 80% of users, the other 16 belong behind "More options."
