---
title: Notification Content Framework
domain: patterns
tags: [notifications, push, email, in-app, sms, alerts, engagement]
sources:
  - "Nielsen Norman Group. Notification UX Research"
  - "Material Design. Notifications"
  - "Apple HIG. Notifications"
---

### Notification Anatomy

Every notification has the same basic structure:

```
[Icon/Avatar] [Title]                    [Timestamp]
              [Body text]
              [Action button(s)]
```

**Title:** WHO did WHAT (or WHAT happened)
**Body:** Details, context, or consequence
**Action:** What to do about it

### The Five Notification Types

**1. Transactional** — Something the user did or requested
```
"Order confirmed — #12345"
"Your payment of $49.99 was received."
[View order]

Rules: Must send. Can't opt out. Be specific and confirming.
```

**2. Informational** — Status updates and changes
```
"Your package is out for delivery"
"Estimated arrival: today by 8 PM."
[Track package]

Rules: User expects these. Be timely and actionable.
```

**3. Social** — Activity from other people
```
"Sarah commented on your post"
"'Great work on the Q3 report!'"
[View comment] / [Reply]

Rules: Include the person's name. Show a preview of the content.
```

**4. Promotional** — Marketing and engagement
```
"New feature: Team workspaces"
"Collaborate with your team in real-time."
[Try it now]

Rules: Lowest priority. Must be opt-in. Easiest to mute. Add real value.
```

**5. Urgent/Alert** — Requires immediate attention
```
"Security alert: New sign-in from unknown device"
"If this wasn't you, secure your account immediately."
[Review activity] / [Secure account]

Rules: Must be impossible to miss. Clear escalation path. Don't cry wolf.
```

### Channel-Specific Writing Rules

**Push notifications (mobile):**
- Title: 40-50 characters max
- Body: 80-120 characters max
- Must make sense without opening the app
- Lead with the most important word
- Action button: 1-2 words
- Example: "Sarah shared a file with you — Q3 Report.pdf"

**In-app notifications:**
- Can be longer and richer than push
- Include contextual actions (reply, approve, dismiss)
- Group related notifications: "3 new comments on your post"
- Support mark-as-read and bulk actions
- Example: "Alex requested your review on 'Homepage Redesign'. Review now or snooze."

**Email notifications:**
- Subject line: the notification itself (40-60 chars)
- Preview text: additional context (80-100 chars)
- Body: full details + clear CTA button
- Always include unsubscribe link
- Example subject: "Your monthly report is ready"
- Example preview: "Revenue up 12% — see the full breakdown"

**SMS:**
- 160 characters maximum (1 segment)
- No formatting — plain text only
- Include sender identification
- Provide opt-out: "Reply STOP to unsubscribe"
- Example: "[AppName] Your verification code is 847291. It expires in 10 minutes."

### The Notification Urgency Matrix

| Urgency | Channel | Timing | Can snooze? | Examples |
|---------|---------|--------|-------------|---------|
| **Critical** | Push + in-app + email | Immediately | No | Security alert, payment failure |
| **High** | Push + in-app | Within minutes | 1 hour | Direct message, deadline approaching |
| **Medium** | In-app + email digest | Within hours | Yes | Comment, status change |
| **Low** | In-app only or digest | Next session | Yes | Weekly summary, feature announcement |

### Notification Grouping

When multiple notifications of the same type occur:
- 2-3: Show individually with sender names
- 4-10: Group with count: "5 new messages in #design"
- 10+: Summarize: "12 people reacted to your post"

**Grouping patterns:**
- By sender: "Sarah sent 3 messages"
- By topic: "5 updates on 'Project Alpha'"
- By type: "8 new comments"
- By time: "3 notifications while you were away"

### Writing Rules

1. **Frontload the key info.** Push notifications may be truncated — the first 5 words must convey meaning.
2. **Use the person's name.** "Sarah commented" not "Someone commented."
3. **Be specific about the object.** "commented on 'Q3 Report'" not "commented on your document."
4. **Action verbs.** "shared," "commented," "approved," "invited" — not "there was activity on."
5. **Don't stack notifications.** If you're sending 5 notifications in 5 minutes, you're doing it wrong. Batch them.
6. **Respect time zones.** Never send non-urgent push notifications outside business hours.
7. **Every notification needs an off switch.** Notification preferences should be granular.

### Anti-Patterns

- **The non-notification:** "Check out what's new!" — no specific content, pure engagement bait
- **The anxiety factory:** "You haven't posted in 3 days!" — guilt-tripping is a dark pattern
- **The fire hose:** 20 push notifications per day — users will turn off ALL notifications
- **The mystery:** "Something happened!" — tell me WHAT happened
- **The novel:** 5-paragraph push notification — it will be truncated and ignored
- **The fake urgency:** "LIMITED TIME!" for something available forever
