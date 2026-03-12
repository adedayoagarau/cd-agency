---
title: Form Content Design Patterns
domain: patterns
tags: [forms, validation, labels, placeholders, inputs, microcopy]
sources:
  - "Wroblewski, L. (2008). Web Form Design"
  - "Baymard Institute. Form Usability Research"
  - "Nielsen Norman Group. Form Design Guidelines"
---

### Core Principle

Forms are conversations. Every field is a question, every input is an answer, every error is a misunderstanding. Good form content makes this conversation feel natural, fast, and forgiving.

### Label Patterns

**Rule: Every field needs a visible, persistent label. Always.**

| Pattern | Example | When to use |
|---------|---------|-------------|
| **Label above field** | "Email address" above the input | Default — fastest completion, fewest errors |
| **Label left of field** | "Email:" next to the input | Dense forms, data entry (desktop only) |
| **Floating label** | Label moves from inside to above on focus | Space-constrained, but only if well-implemented |
| **Label inside (placeholder only)** | Gray "Email" inside the input | NEVER as the only label — disappears on input |

**Label writing rules:**
- Use nouns, not instructions: "Email address" not "Enter your email"
- Be specific: "Work email" or "Personal email" not just "Email"
- Match the user's vocabulary: "Phone number" not "Contact telephone"
- Include format hints in the label if needed: "Date of birth (MM/DD/YYYY)"

### Placeholder Text

Placeholders are supplementary hints, never replacements for labels.

**Good uses:**
- Format examples: `e.g., name@company.com`
- Clarifying hints: `e.g., "Acme Corp"`
- Search suggestions: `Search by name, email, or ID`

**Never use placeholders for:**
- The only label (disappears on focus)
- Instructions (users think the field is pre-filled)
- Critical information (invisible once typing begins)

### Help Text and Descriptions

Place help text below the field, visible before the user interacts.

```
[Label: Password]
[Input field]
Must be at least 8 characters with one number and one special character.
```

**When to use help text:**
- Format requirements: "Use MM/DD/YYYY format"
- Privacy reassurance: "We'll only use this to send your receipt"
- Constraints: "Maximum 500 characters (342 remaining)"
- Context: "This will be visible on your public profile"

### Required vs. Optional Fields

**Rule:** Mark the minority. If most fields are required, mark optional ones. If most are optional, mark required ones.

| Approach | When to use | Pattern |
|----------|-------------|---------|
| Mark optional | Most fields required | "Company name (optional)" |
| Mark required | Most fields optional | "Email address *" with "* Required" legend |
| Remove optionals | Always worth considering | Fewer fields = higher completion |

**Never use asterisks without a legend.** New users don't know `*` means required.

### Inline Validation Messages

**Timing:**
- Validate on blur (when user leaves the field), not on every keystroke
- Exception: password strength can update in real-time
- Never validate an empty field before the user has typed anything

**Success patterns:**
- Checkmark icon (no text needed for simple fields)
- "Looks good!" or "Available!" for username/email checks
- Green border on the field

**Error patterns:**
- Red border on the field + error message below
- Specific, actionable: "Enter at least 8 characters" not "Invalid input"
- Don't clear what the user typed — they may be close to right
- Persist until the error is fixed (don't auto-dismiss)

### Common Field Patterns

**Email:**
```
Label: "Email address"
Placeholder: "e.g., name@company.com"
Validation: "Enter a valid email address"
```

**Password (create):**
```
Label: "Password"
Help text: "At least 8 characters with one number"
Strength indicator: Weak / Fair / Strong / Very strong
Validation: "Password is too short (8 characters minimum)"
```

**Password (sign in):**
```
Label: "Password"
Link: "Forgot password?" (right-aligned)
Validation: "Wrong email or password" (combined, for security)
```

**Phone number:**
```
Label: "Phone number"
Placeholder: "(555) 123-4567"
Help text: "We'll text you a verification code"
Validation: "Enter a valid phone number"
```

**Address:**
```
Label each line separately: "Street address" / "Apartment, suite, etc. (optional)" / "City" / "State" / "ZIP code"
Use autocomplete attributes for browser autofill
Consider address lookup: "Start typing your address..."
```

**Credit card:**
```
Label: "Card number"
Trust signals: Lock icon + "Secure payment"
Placeholder: "1234 5678 9012 3456" (formatted)
Auto-format as they type: "1234 5678..."
Error: "Check your card number" (don't say "invalid")
```

### Multi-Step Forms

- **Progress indicator:** "Step 2 of 4 — Payment details"
- **Step titles:** Should describe what the user does, not form sections: "Tell us about yourself" not "Personal information"
- **Back button:** Always available, preserving entered data
- **Save progress:** "We'll save your progress. You can finish later."
- **Summary before submission:** Show all entered data for review

### Submit Button Patterns

| Context | Bad | Good |
|---------|-----|------|
| Account creation | "Submit" | "Create account" |
| Payment | "Submit" | "Pay $49.99" |
| Contact form | "Submit" | "Send message" |
| Search | "Submit" | "Search" |
| Newsletter | "Submit" | "Subscribe" |
| Settings | "Submit" | "Save changes" |

**Rule:** The submit button should tell the user exactly what will happen when they click it.

### Reducing Form Length

Every field you remove increases completion rate. Ask:
1. Do we really need this? Can we get it later?
2. Can we infer it? (Country from IP, name from email profile)
3. Can we combine fields? (Full name vs. First + Last)
4. Can we use smart defaults? (Pre-select the most common option)
5. Can we delay optional fields? (Collect after account creation)

**Baymard Institute finding:** Reducing checkout forms from 15 to 7 fields improved completion by 26%.
