---
title: UI Content Patterns Library
domain: patterns
tags: [patterns, modals, confirmations, loading, success, empty-states, tooltips]
sources:
  - "Material Design. Communication Guidelines"
  - "Polaris Design System. Content Guidelines"
  - "Apple Human Interface Guidelines"
---

### Modals and Dialogs

**Information modal:**
```
Title:  [What this is about] — noun phrase
Body:   [Details the user needs] — 1-3 sentences
Action: [Primary CTA] / [Dismiss]

Example:
Title:  "What's new in version 3.0"
Body:   "We've added dark mode, faster search, and team sharing."
Action: [See what's new] / [Dismiss]
```

**Confirmation modal (non-destructive):**
```
Title:  [Action question] — "Save changes?"
Body:   [What happens] — "Your draft will be saved and you can edit it later."
Action: [Confirm verb] / [Cancel]

Example:
Title:  "Save changes?"
Body:   "You have unsaved changes to this document."
Action: [Save changes] / [Discard]
```

**Destructive confirmation modal:**
```
Title:  [Specific destructive action] — "Delete this project?"
Body:   [Irreversible consequence] — "This will permanently delete all 24 files and remove access for 3 team members. This cannot be undone."
Action: [Exact verb matching title] / [Safe escape]

Example:
Title:  "Delete this project?"
Body:   "All 24 files and 3 team members' access will be permanently removed. This cannot be undone."
Action: [Delete project] / [Keep project]
```

**Rules:**
- Title = action or question, never "Are you sure?"
- Body = consequences, not instructions
- Primary button = verb matching the title
- Secondary button = clearly the safe option
- For destructive: require typing the name for high-stakes actions

### Loading and Progress States

**Determinate (known duration):**
```
Progress bar + "Uploading... 3 of 10 files (45%)"
Finishing: "Almost done..."
Complete: "Upload complete. 10 files added."
```

**Indeterminate (unknown duration):**
```
Spinner + context: "Loading your dashboard..."
Long wait: "This is taking longer than usual. Hang tight."
Very long: "Still working on it. This usually takes 1-2 minutes."
```

**Skeleton screens:** No text needed — the visual placeholder communicates loading.

**Background processing:**
```
"We're processing your data. We'll email you when it's ready."
"Your export is being prepared. You can close this page."
```

**Rules:**
- Always communicate what's loading (not just a spinner)
- For long operations, show progress or time estimate
- Let users continue other tasks when possible
- Success state should explicitly confirm completion

### Success Messages

**Inline success:**
```
"Changes saved" / "Message sent" / "Payment received"
Brief, specific, past tense (confirms completion)
Auto-dismiss after 3-5 seconds
```

**Success page (for major actions):**
```
Headline: "You're all set!" / "Order confirmed"
Details: Specifics (order number, next steps)
Next action: What to do next ("View your order" / "Back to dashboard")
```

**Rules:**
- Use past tense for completed actions: "Sent" not "Sending"
- Be specific: "Invoice sent to john@example.com" not just "Done"
- For transactions: include reference number and receipt option
- For complex flows: summarize what was accomplished

### Tooltips

**Pattern:** Answer ONE question in under 60 characters.

```
Good: "Last updated 2 hours ago"
Good: "Only you can see this"
Good: "Keyboard shortcut: Ctrl+S"
Bad:  "This feature allows you to configure the settings for your notification preferences across all channels and devices"
```

**When to use tooltips:**
- To explain an icon or abbreviated label
- To show keyboard shortcuts
- To provide supplementary context for a setting
- To define a term the user might not know

**When NOT to use tooltips:**
- For essential information (not accessible on touch devices)
- As the primary label (use a real label)
- For lengthy explanations (use help text or a link)
- For error messages (use inline validation)

### Banners and Alerts

**Info banner:**
```
"New: Team workspaces are now available. [Learn more]"
Dismissible, blue/neutral
```

**Warning banner:**
```
"Your trial ends in 3 days. [Upgrade now] to keep your data."
Persistent until resolved, amber/yellow
```

**Error banner:**
```
"We're experiencing issues with file uploads. We're working on a fix."
Persistent until resolved, red
```

**Success banner:**
```
"Your account has been verified."
Auto-dismiss after 5-8 seconds, green
```

### Badges and Status Labels

**Status progression:**
```
Draft → Pending → In Review → Approved → Published
Pending → Processing → Shipped → Delivered
Open → In Progress → Resolved → Closed
```

**Rules:**
- Use consistent verb forms (all past participles, or all present)
- Color code: gray (neutral), blue (active), yellow (attention), green (success), red (error)
- Keep to 1-2 words maximum
- Status should tell the user what happened, not what they should do

### Onboarding Patterns

**Welcome message:**
```
"Welcome to [Product], [Name]! Let's get you set up."
+ Primary CTA: "Get started"
+ Skip option: "I'll explore on my own"
```

**Checklist:**
```
"Get started with [Product]"
✓ Create your profile
○ Invite your team
○ Create your first project
○ Connect an integration
"2 of 4 complete"
```

**Tooltip tour:**
```
Step 1: "This is your dashboard. You'll see your projects here." [Next]
Step 2: "Create new projects with this button." [Next]
Step 3: "Invite team members from settings." [Got it]
+ "Step 2 of 3" + [Skip tour]
```

### Empty States (by type)

**First use:**
```
Illustration + "No projects yet"
"Create your first project to get started."
[Create project]
```

**No results (search/filter):**
```
"No results for '[query]'"
"Try adjusting your filters or search for something else."
[Clear filters]
```

**User-cleared:**
```
"All caught up!"
"You've read all your notifications."
(No CTA needed — this is a success state)
```

**Error-caused:**
```
"Couldn't load your data"
"Check your connection and try again."
[Retry]
```
