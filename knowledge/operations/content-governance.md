---
title: Content Governance and Style Guide Management
domain: operations
tags: [governance, style-guide, terminology, consistency, workflow, review]
sources:
  - "Bloomstein, M. (2012). Content Strategy at Work"
  - "Halvorson, K. (2012). Content Strategy for the Web"
  - "Mailchimp Content Style Guide"
---

### Core Principle

Content governance is the system that ensures content stays consistent, accurate, and on-brand across every screen, every writer, and every update. Without governance, even the best content design degrades over time as teams grow, features multiply, and writers change.

### The Four Pillars of Content Governance

**1. Style guide** — The single source of truth for how to write
**2. Terminology** — Controlled vocabulary and word lists
**3. Review process** — Who reviews content and when
**4. Maintenance** — How content is kept current

### Building a Content Style Guide

**Essential sections:**

| Section | What it covers | Example |
|---------|---------------|---------|
| **Voice and tone** | Brand personality, tone by context | "Confident but not cocky" |
| **Grammar and mechanics** | Capitalization, punctuation, numbers | "Use sentence case for headings" |
| **Word list** | Always/never use terms | "Use 'sign in,' never 'log in'" |
| **Component patterns** | Standard text per UI component | "Error messages use the three-part formula" |
| **Accessibility** | Inclusive writing rules | "Don't use color alone to convey meaning" |
| **Formatting** | Lists, links, dates, times, currency | "Dates: March 15, 2024 (not 03/15/2024)" |
| **Platform-specific** | Mobile vs. desktop, OS differences | "'Tap' on mobile, 'click' on desktop" |

**Style guide maintenance:**
- Review quarterly at minimum
- Version it (changes should be tracked and announced)
- Make it searchable (not a PDF — a living document or wiki)
- Include real examples from the product, not hypothetical ones

### Terminology Management

**Build a controlled vocabulary:**

| Term | Use | Don't use | Notes |
|------|-----|-----------|-------|
| Sign in | ✓ | Log in, Login, Sign on | Two words as a verb, one word as a noun (sign-in) |
| Workspace | ✓ | Project, Space, Area | Our main organizational concept |
| Team member | ✓ | User, Person, Account holder | People, not accounts |
| Remove | ✓ | Delete (for team members) | "Delete" for permanent data actions only |
| Save | ✓ | Apply, Submit, Update | For preserving changes |

**Rules for terminology:**
- One concept = one word. Never use synonyms for the same thing.
- Match user language, not engineering language. "Projects" not "workspaces" if users say "projects."
- Audit regularly. New features introduce new terms that may conflict.
- Share with engineering. Code variable names should match UI labels when possible.

### Content Review Process

**Pre-publish review checklist:**
1. Is the content accurate? (verified by subject matter expert)
2. Does it match the style guide? (voice, tone, terminology)
3. Is it accessible? (reading level, inclusive language, screen reader compatible)
4. Is it consistent? (matches existing patterns for this component type)
5. Has it been tested? (in context, at actual size, on mobile)

**Review roles:**
- **Content designer:** Primary author, owns quality
- **Peer reviewer:** Another content designer checks for consistency
- **Subject matter expert:** Verifies technical accuracy
- **Accessibility reviewer:** Checks inclusive design
- **Legal (if needed):** Reviews compliance-sensitive content

**When to require review:**
- **Always:** User-facing error messages, legal/privacy content, pricing
- **Usually:** Onboarding, CTAs, notifications, empty states
- **Sometimes:** Tooltip text, minor label changes, help articles
- **Optional:** Internal tools, admin-only content, dev documentation

### Content Lifecycle Management

**Creation → Review → Publish → Monitor → Update → Retire**

| Phase | Action | Owner |
|-------|--------|-------|
| **Creation** | Draft content following patterns | Content designer |
| **Review** | Peer review + style guide check | Content team |
| **Publish** | Deploy with the feature | Engineering + Content |
| **Monitor** | Track metrics, gather feedback | Content + Product |
| **Update** | Revise based on data and feedback | Content designer |
| **Retire** | Remove outdated content | Content + Product |

**Content debt indicators:**
- Inconsistent terminology across screens
- Error messages that reference removed features
- Help articles for features that have changed
- Outdated screenshots or examples
- Placeholder text that shipped to production

### Scaling Content Design

**For small teams (1-3 content designers):**
- Style guide in a shared doc
- Informal peer review
- Direct collaboration with designers/engineers

**For medium teams (4-10):**
- Published style guide (Notion, wiki, or dedicated tool)
- Formal review process with checklists
- Component-based content patterns
- Regular content syncs/critiques

**For large teams (10+):**
- Content design system (integrated with visual design system)
- Automated linting and style checking (tools like this one)
- Content ops role: manages governance, tools, and process
- Localization workflow with terminology management
- Content analytics dashboard

### Tools for Content Governance

- **Style guide platforms:** Frontitude, Writer, Ditto, Google Docs
- **Terminology management:** Termbase, shared spreadsheets, integrated glossaries
- **Content linting:** Vale, textlint, custom rules (like cd-agency's linter)
- **Version control:** Git-based content management for technical teams
- **Design system integration:** Figma with content components, Storybook with real copy
