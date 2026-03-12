---
title: "Clarifying Questions Framework for Content Designers"
domain: frameworks
tags: [questions, discovery, context, brief, requirements, stakeholders]
relevance: all
---

## The Art of Asking Before Writing

The biggest mistake in content design is writing too soon. Great content comes from great questions. Before generating any content, identify what you don't know — then ask.

### Why Questions Matter

- **Vague input → generic output.** "Write an error message" produces something mediocre. "Write an error message for a non-technical user who just tried to upload a 500MB file on mobile over 3G" produces something specific and useful.
- **Assumptions kill quality.** If you assume "mobile" when the user means "desktop," every character limit, layout decision, and interaction pattern is wrong.
- **Context separates junior from senior.** Junior writers take the brief and write. Senior writers interrogate the brief, discover the real problem, and THEN write.

### The Universal Question Set

Ask these for EVERY content request, regardless of type:

**1. Who is the user?**
- What's their technical sophistication? (Non-technical consumer? Developer? Admin?)
- Are they a first-time user or experienced?
- What's their emotional state right now? (Calm, frustrated, anxious, excited, in a hurry?)
- Are they a native English speaker? (Affects vocabulary complexity)

**2. Where does this content live?**
- What UI element? (Button, modal, tooltip, notification, page, form, etc.)
- What platform? (iOS, Android, web, desktop app, email, SMS)
- What screen size? (Phone, tablet, desktop, responsive)
- What's around it? (Other text, images, icons, whitespace)

**3. What's the user trying to do?**
- What task brought them to this screen?
- What did they do right before seeing this?
- What should they do after?
- What happens if they do nothing?

**4. What are the constraints?**
- Character limits? (Hard limit or soft guideline?)
- Will this be translated/localized?
- Are there accessibility requirements? (WCAG level)
- Are there legal/compliance requirements?
- Is there a brand voice guide?

**5. What does success look like?**
- What action should the user take?
- How will you measure if this content worked? (Click-through? Completion? Reduced support tickets?)
- Is this meant to inform, persuade, instruct, or reassure?

### Specialist Question Sets

Beyond the universal questions, each content type demands specific questions:

**For Error Messages:**
- Is this a user error or system error?
- Can the user fix it themselves, or do they need support?
- Is this blocking (they can't proceed) or informational (they can dismiss and continue)?
- What's the error frequency? (Rare edge case or happens to 20% of users?)
- What's the severity? (Data loss risk? Security issue? Minor inconvenience?)
- Is there a fallback or alternative path?

**For CTAs/Buttons:**
- Is this the primary or secondary action?
- What's the commitment level? (Free action vs. payment vs. irreversible)
- What's the user's awareness level? (Do they already want this, or do you need to persuade them?)
- What's above the CTA? (Headline + supporting copy set up the click)
- What's the anxiety? (What might make them hesitate?)

**For Onboarding:**
- What's the "aha moment"? (When does the user first feel the product's value?)
- How many steps can you afford? (Each step loses ~20% of users)
- Is this self-serve or supported? (Can they skip and figure it out later?)
- What data do you NEED vs. what's nice-to-have? (Minimize upfront friction)
- What's the user's prior experience with similar products?

**For Notifications:**
- Is this worth interrupting someone's day?
- What happens if they miss it? (Urgency vs. convenience)
- What channels are available? (Push, email, in-app, SMS)
- How frequently will this type of notification fire? (Daily? Weekly? Once?)
- Can the user control this notification? (Preferences, mute, unsubscribe)

**For Empty States:**
- Why is this empty? (First-time use, no results, user cleared it, error)
- What should the user do about it? (Create something? Adjust filters? Wait?)
- Is this permanent or temporary? (Will content appear later?)
- Is this a critical section or an optional feature?

**For Forms:**
- How many fields total? (More fields = more abandonment)
- Which fields are truly required vs. nice-to-have?
- Will users know what to enter? (Do they need examples or help text?)
- Are there format requirements? (Phone number format, password rules)
- What happens on error? (Inline validation? After submit?)

**For Mobile Content:**
- Is this a native app or mobile web?
- What's the exact viewport width?
- Is this content that also exists on desktop? (Adapting vs. creating new)
- Will the user be holding the phone with one hand or two?
- Is there an offline or slow-network scenario?

### How to Use These Questions

**If you have the answers** → Use them to constrain and focus your output. Mention the constraints in your response so the user knows you're designing with intent.

**If you DON'T have the answers** → Ask. List the 3-5 most critical missing pieces and explain WHY each matters. For example:

> "Before I write this error message, I need to know:
> 1. **Who sees this?** A technical user gets 'API rate limit exceeded (429).' A consumer gets 'You're sending requests too fast. Wait a moment and try again.'
> 2. **What can they do?** If they can retry, I'll include a retry button. If they need to contact support, I'll include a link.
> 3. **Where does this appear?** An inline message has ~80 characters. A modal can have 200+."

**If the user says "just write it"** → Make your assumptions explicit. State them clearly at the top of your output:

> "**Assumptions I'm making:** Desktop web, non-technical consumer, no character limit specified (I'll target 80 chars), English-only, WCAG AA compliance. Let me know if any of these are wrong."

### The 3-Question Shortcut

If you can only ask three questions, ask these:

1. **Who is the user and what's their state of mind?** (Determines vocabulary, tone, and complexity)
2. **What element and platform is this for?** (Determines character budget and conventions)
3. **What should they do next?** (Determines the CTA and information hierarchy)

These three questions alone will transform generic content into specific, useful content.
