---
title: Error Message Taxonomy and Patterns
domain: patterns
tags: [errors, taxonomy, validation, recovery, patterns]
sources:
  - "Nielsen Norman Group. Error Message Guidelines"
  - "Yifrah, K. (2017). Microcopy: The Complete Guide"
  - "Material Design. Communication: Confirmation & Acknowledgement"
---

### Error Categories

Every error falls into one of these categories. Each requires a different content approach.

**1. Validation Errors** — User input doesn't meet requirements
```
Pattern: [What's wrong] + [How to fix it]
Tone: Helpful, instructive — the system is teaching, not scolding

Examples:
- "Enter a valid email address (e.g., name@example.com)"
- "Password must be at least 8 characters"
- "Phone number should include area code"
- "This field is required"

Rules:
- Show inline, next to the field
- Appear on blur or submit, not on every keystroke
- Red border on the field + message below
- Never clear the user's input
```

**2. Authentication Errors** — Identity or permission problems
```
Pattern: [What happened] + [What to do] + [Escape hatch]
Tone: Neutral, secure — don't reveal what specifically failed

Examples:
- "Wrong email or password. Try again, or reset your password."
- "Your session has expired. Sign in again to continue."
- "You don't have permission to view this page. Contact your admin."
- "Too many sign-in attempts. Try again in 15 minutes."

Rules:
- NEVER specify which field was wrong (security risk)
- Always offer password reset as an escape
- Account lockout: give a specific time ("15 minutes" not "later")
- Don't reveal whether an email exists in the system
```

**3. Network/Connectivity Errors** — Communication failures
```
Pattern: [What happened] + [Likely cause] + [Automatic retry or manual action]
Tone: Reassuring — it's probably temporary

Examples:
- "Can't connect. Check your internet and try again."
- "Taking longer than usual. We'll keep trying."
- "Connection lost. Your changes are saved locally."
- "Server is temporarily unavailable. Try again in a few minutes."

Rules:
- Distinguish between user's connection and server issues
- Auto-retry with visual indicator when possible
- Preserve user's work (draft saving)
- Offer offline mode if available
```

**4. Server/System Errors** — Backend failures
```
Pattern: [Something went wrong] + [It's not you] + [What we're doing / what you can do]
Tone: Honest, reassuring — take responsibility

Examples:
- "Something went wrong on our end. We're working on it."
- "We're having trouble right now. Try again in a few minutes."
- "Couldn't process your request. Your payment was not charged."
- "Our servers are getting more traffic than usual. Please try again shortly."

Rules:
- Never expose stack traces, error codes as primary message
- Explicitly state if money/data was NOT affected
- Give time estimates when possible
- Provide status page link for major outages
```

**5. Not Found Errors** — Missing resources
```
Pattern: [What's missing] + [Why it might be missing] + [Where to go instead]
Tone: Helpful, redirecting — guide them somewhere useful

Examples:
- "This page doesn't exist. It may have been moved or deleted."
- "We couldn't find that file. It may have been removed by the owner."
- "No account found with that email. Would you like to sign up?"
- "This link has expired. Request a new one."

Rules:
- Offer search or navigation to help them find what they need
- If the URL looks like a typo, suggest the correct page
- Show recently visited or popular pages
```

**6. Rate Limit / Quota Errors** — Usage limits exceeded
```
Pattern: [What limit was hit] + [When it resets] + [How to get more]
Tone: Factual, transparent — limits are fair boundaries

Examples:
- "You've reached your daily upload limit (10 files). Resets tomorrow at midnight."
- "Free plan allows 3 projects. Upgrade for unlimited projects."
- "Too many requests. Please wait 60 seconds."
- "You've used 100% of your storage. Delete files or upgrade your plan."

Rules:
- Show the limit clearly (X of Y)
- Always show when it resets
- Offer upgrade path without being pushy
- Distinguish between hard limits and soft limits
```

**7. Destructive Action Warnings** — Preventing irreversible mistakes
```
Pattern: [What will happen] + [What you'll lose] + [Confirm verb matching the action]
Tone: Serious, precise — no ambiguity about consequences

Examples:
- "Delete this project? All 24 files and 3 team members' access will be permanently removed."
- "Cancel your subscription? You'll lose access to premium features on April 1."
- "Remove this team member? They'll lose access to all shared projects."

Rules:
- Button label must match the action: "Delete project" / "Keep project"
- Never use "OK" for destructive actions
- Quantify what will be lost (number of files, members, data)
- Offer alternatives: "Archive instead?" or "Download your data first"
```

### The Three-Part Error Formula

Every error message should answer three questions:
1. **What happened?** — State the problem clearly
2. **Why?** — Brief explanation (if it helps the user)
3. **What now?** — Specific action to resolve it

```
What:  "Your file couldn't be uploaded."
Why:   "It's larger than the 10 MB limit."
Fix:   "Compress the file or choose a smaller one."
```

### Error Severity Scale

| Severity | Visual | Blocks user? | Examples |
|----------|--------|-------------|----------|
| **Info** | Blue/neutral icon | No | "You're editing an older version" |
| **Warning** | Yellow/amber icon | No | "Your subscription expires in 3 days" |
| **Error** | Red icon | Yes (for that action) | "Wrong password" |
| **Critical** | Red banner, prominent | Yes (completely) | "Service unavailable" |

### Anti-Patterns

- **Blame the user:** "You entered an invalid email" → "Enter a valid email address"
- **Be vague:** "An error occurred" → "Your payment couldn't be processed"
- **Use error codes alone:** "Error 403" → "You don't have access to this page"
- **Use jargon:** "Null reference exception" → "Something went wrong"
- **Double negative:** "Cannot not proceed" → clear, direct statement
- **Scream:** "ERROR!!!" → calm statement of fact
