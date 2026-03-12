---
title: Voice UI Content Patterns
domain: emerging
tags: [voice-ui, smart-speaker, alexa, siri, google-assistant, audio, conversational]
sources:
  - "Amazon. Alexa Design Guide"
  - "Google. Conversation Design Guidelines"
  - "Apple. SiriKit Design Guidelines"
  - "Cathy Pearl (2016). Designing Voice User Interfaces"
---

### Core Principle

Voice-only interfaces strip away all visual cues. There are no buttons, no bold text, no layout. Words ARE the entire interface. Every word must carry its weight — there is no scrolling back to re-read.

### Key Differences from Visual UI

| Visual UI | Voice UI |
|-----------|----------|
| Users scan and select | Users listen and remember |
| Can show 20 options | Max 3-5 options at a time |
| Errors visible on screen | Errors must be spoken aloud |
| User sets the pace (scrolling) | System sets the pace (speech rate) |
| Can refer back to earlier content | Everything is ephemeral |
| Icons and layout carry meaning | Only words carry meaning |

### Writing for the Ear

**1. Front-load the answer.**
- Visual: "To check your balance, go to Settings > Account > Balance"
- Voice: "Your balance is $1,234.56. Would you like to do anything else?"

**2. Shorter is critical.**
- Visual error: "Your password must be at least 8 characters and include one uppercase letter, one number, and one special character."
- Voice error: "Passwords need at least 8 characters with a number and special character. Try again."

**3. Use natural speech patterns.**
- Don't say: "Select option 1, 2, or 3"
- Say: "Would you like to check your balance, make a transfer, or something else?"

**4. Avoid homophone confusion.**
- "To" / "Two" / "Too" — rephrase to avoid confusion
- "Their" / "There" — context must make it unambiguous
- Numbers: "Fifteen" not "Fifty" when disambiguation matters

### Conversation Flow Patterns

**Opening/greeting:**
```
"Welcome back, Sarah. What can I help you with?"
NOT: "Hello! I'm your AI assistant. I can help with many things. What would you like to do today?"
```

**Offering choices (max 3):**
```
"I found 3 Italian restaurants nearby. The closest is Bella's, half a mile away. Would you like directions, or should I read the next option?"
NOT: "I found 47 Italian restaurants. Here they are..."
```

**Confirmation:**
```
"Setting a timer for 15 minutes. Is that right?"
"Sending $50 to Alex. Should I go ahead?"
```

**Error recovery:**
```
"I didn't catch that. Could you say it again?"
"I heard 'fifty.' Did you mean $50 or 50 items?"
"I'm not sure I can help with that. Try asking about [supported topics]."
```

**Ending a conversation:**
```
"All done. Your alarm is set for 7 AM."
"Anything else? ... Okay, have a good day!"
NOT: "Transaction complete. Session terminated."
```

### Platform-Specific Patterns

**Alexa (Amazon):**
- Responses should be under 8 seconds of speech
- Use SSML for pronunciation, pauses, emphasis
- "Skill" invocation: "Alexa, ask [Skill Name] to [action]"
- Card companion: send visual supplement to the Alexa app

**Google Assistant:**
- Supports "rich responses" with visual cards on screens
- Conversation can be multi-turn naturally
- "Hey Google, [direct action]" — no skill invocation needed
- Chips: suggest follow-up actions visually when screen available

**Siri (Apple):**
- Tight integration with device features (timers, messages, calls)
- "Shortcuts" for custom voice commands
- Responses are brief — Apple prioritizes speed over verbosity
- System-level voice: matches Apple's direct, clean tone

### Multimodal Design (Voice + Screen)

When a device has both voice and screen:
- **Voice delivers the answer.** Screen shows supporting details.
- **Voice confirms.** Screen shows the full list/receipt/details.
- **Voice navigates.** Screen responds visually.
- **Never read what's on screen.** "Here are your results" + screen shows the list.

### Accessibility in Voice UI

- **Speak clearly and at a natural pace** — avoid cramming too much into one response
- **Offer alternative input** — "You can also say the number, or press it on the keypad"
- **Support interruption** — users should be able to cut in without waiting for the system to finish
- **Provide recaps** — "Just to confirm: you want to order a large pepperoni pizza for delivery to 123 Main Street"
- **Timeout gracefully** — "Are you still there? I'll wait a moment. Say 'help' if you need options."

### Anti-Patterns

- **The robot:** "Processing. Please wait. Request complete." — speak like a person
- **The lecturer:** 30-second monologues — keep responses under 15 seconds
- **The quiz show:** "Was that A, B, or C?" — use natural language, not menu codes
- **The amnesiac:** Forgetting context from 2 turns ago — maintain conversation state
- **The overcautious:** "Are you sure? Are you really sure? Last chance!" — one confirmation is enough
