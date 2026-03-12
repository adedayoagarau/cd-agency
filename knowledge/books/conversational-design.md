---
title: "Conversational Design — Erika Hall"
domain: books
year: 2018
tags: [conversation, dialogue, chatbots, voice-ui, interaction-design]
key_concepts: [conversation as interface, cooperative principle, dialogue patterns, voice UI, chatbot design]
---

### About the Book

Erika Hall's *Conversational Design* argues that all interfaces are conversations — not just chatbots and voice assistants, but every form, button, and screen. Understanding conversation principles makes all interface content better.

### Core Thesis

Every interaction between a user and a system is a conversation. The user asks (types, taps, speaks), the system responds (shows, tells, does). Good conversational design follows the same principles as good human conversation: be clear, be relevant, be helpful, and don't waste the other person's time.

### Grice's Cooperative Principle (Applied to UI)

Philosopher H.P. Grice defined four maxims of effective conversation. Applied to content design:

**1. Maxim of Quantity:** Say enough, but not more than needed.
- UI: Show exactly the information needed at each step. Not less (confusing). Not more (overwhelming).
- Bad: 500-word privacy explanation on a sign-up page
- Good: "We'll never share your email" + link to full policy

**2. Maxim of Quality:** Say only what you believe to be true.
- UI: Don't promise what you can't deliver. Don't use misleading labels.
- Bad: "Instant setup" for something that takes 10 minutes
- Good: "Setup takes about 10 minutes"

**3. Maxim of Relation:** Be relevant.
- UI: Every piece of content should relate to the user's current task.
- Bad: Showing marketing upsells during an error recovery flow
- Good: Error message + fix + "Need help?" link

**4. Maxim of Manner:** Be clear and orderly.
- UI: Logical flow, clear language, no ambiguity.
- Bad: "Your changes may or may not have been saved"
- Good: "Changes saved" or "Changes not saved — try again"

### Conversation Patterns in UI

**Turn-taking:**
Every UI interaction is a turn in a conversation:
1. System presents options (menu, form, prompt)
2. User responds (selection, input, action)
3. System acknowledges (confirmation, result, next step)
4. Repeat

**Repair sequences:**
When misunderstandings happen in conversation, people repair them. In UI:
- Error messages ARE repair sequences
- "Did you mean...?" is a classic conversational repair
- Undo is the UI equivalent of "Wait, scratch that"
- Confirmation dialogs are "Just to clarify..."

**Grounding:**
In conversation, people confirm shared understanding. In UI:
- Summary screens before final submission
- "You're signing up for the Pro plan at $29/month"
- Order review before purchase
- "Your email is john@example.com" — let users verify

### Chatbot and Voice UI Specific Principles

**Set expectations early:**
- "I can help with orders, returns, and account questions."
- Users need to know the boundaries of the conversation
- Under-promise capability to avoid frustration

**Provide escape hatches:**
- "Talk to a human" should always be available
- Don't trap users in loops
- If the bot can't help: acknowledge it and hand off gracefully

**Handle the unexpected:**
- Users will say things the bot doesn't expect
- "I'm not sure I understand. Could you rephrase that?" > silence or generic error
- Always have a graceful fallback

**Personality with restraint:**
- Chatbot personality should serve function, not performance
- A helpful, clear bot > a witty, confusing bot
- Match the tone to the task: customer service bots should be calm and efficient

### Actionable Takeaways

- **Treat every screen as a turn in a conversation.** What did the user just "say" (do)? What should you "say" back?
- **Apply Grice's maxims as a content audit.** Is this content truthful, relevant, clear, and the right amount?
- **Confirmation is a conversation skill.** Repeat back important information before proceeding.
- **Repair gracefully.** Error messages should feel like a helpful correction, not a punishment.
- **Know the conversation's limits.** Design clear paths for when the conversation (automated or not) can't continue.
