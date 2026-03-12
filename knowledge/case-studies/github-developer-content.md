---
title: "Case Study: GitHub — Developer Content Design"
domain: case-studies
tags: [developer-experience, documentation, ui-copy, empty-states, notifications]
company: GitHub
---

### Overview

GitHub serves developers with highly technical content that still feels human and approachable. Their content design balances technical precision with warmth — a combination that proves "developer content" doesn't have to mean "cold, robotic content."

### Voice Characteristics

- **Technically precise but not pedantic** — Uses correct terminology but doesn't lecture
- **Warm but not infantilizing** — Treats developers as intelligent adults without being cold
- **Concise but not terse** — Every word counts, but context is provided
- **Community-oriented** — Uses "you" and "your" constantly, references collaboration

### Empty State Excellence

GitHub's empty states are consistently excellent:

**Empty repository:**
"Quick setup — if you've done this kind of thing before" + actual setup commands
- Assumes competence while providing help
- The content IS the functionality (copy-paste commands)

**No pull requests:**
"There aren't any open pull requests."
- Then shows filters and a clear "New pull request" button
- Content explains + action is one click away

**No issues:**
"There aren't any open issues."
- For repos with issue templates: shows template options
- The empty state transitions seamlessly into the creation flow

### Error Handling

**404 page:**
"This is not the web page you are looking for." + the Octocat illustration
- Personality in error states (low-stakes error — page not found)
- Clear action: search bar and link to homepage

**Repository access denied:**
"You don't have access to this repository. Contact the owner to request access."
- Clear what happened (no access)
- Clear what to do (contact owner)
- No blame, no technical jargon

**Git push errors:**
"Your branch is behind 'origin/main' by 3 commits. Pull before pushing."
- Specific (3 commits, which branch)
- Actionable (pull first)
- Uses git terminology appropriately (the audience knows it)

### Content Design Patterns

**Contextual help:**
- Inline explanations for complex settings: "Allow merge commits: Combine all commits from the head branch into a single commit in the base branch."
- These explain WHAT the setting does, not just label it

**Progressive disclosure in settings:**
- Repository settings show the most common options first
- Advanced features (branch protection rules, webhooks) are accessible but not prominent
- Each advanced feature includes a brief explanation

**Notification content:**
- "@username requested your review on #123"
- Pattern: WHO + ACTION + WHAT (+ CONTEXT)
- Always actionable — clicking goes directly to the thing that needs attention

### Terminology Consistency

GitHub is strict about terminology:
- "Repository" (never "repo" in the UI, though users say it)
- "Pull request" (never "merge request" — that's a competitor's term)
- "Issue" (not "ticket," "bug," or "task")
- "Branch" (consistent metaphor throughout)
- "Fork" (with clear explanation when first encountered)

### Lessons for Content Designers

1. **Know your audience's vocabulary.** GitHub uses git terminology because their users know it. Don't dumb down for experts — but do explain for newcomers.
2. **Empty states are onboarding.** GitHub uses empty states to teach workflows and drive first actions.
3. **Error messages scale by audience.** Git push errors use technical language; 404 pages use plain language. Same product, different contexts.
4. **Functional empty states > decorative ones.** GitHub's empty repo page with copy-paste commands is more useful than any illustration.
5. **Personality should match stakes.** Fun on 404 pages, precise on permission errors, warm on empty states.
