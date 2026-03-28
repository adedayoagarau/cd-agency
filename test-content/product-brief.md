# Vaultline — Product Brief

## Overview
Vaultline is a cloud-based financial operations platform for mid-market SaaS companies (50–500 employees). It consolidates billing, revenue recognition, subscription management, and financial reporting into a single workspace.

## Target Audience
- **Primary**: Finance teams (Controllers, FP&A analysts, Revenue accountants)
- **Secondary**: Product managers tracking usage metrics, Engineering leads managing billing integrations
- **Tertiary**: C-suite executives reviewing dashboards and board reports

## Brand Voice

### Personality
Vaultline speaks like a **trusted senior colleague** — someone who's been through three audits and knows the shortcuts, but never cuts corners. We're precise without being cold, and confident without being condescending.

### Voice Dimensions
| Dimension | Position | Notes |
|-----------|----------|-------|
| Formal ↔ Casual | 65% formal | Professional but not stiff. First-person plural ("we") is fine. |
| Technical ↔ Simple | 55% technical | Finance people know their terms. Don't dumb down "ARR" or "deferred revenue." |
| Authoritative ↔ Friendly | 60% authoritative | Guide, don't lecture. |
| Serious ↔ Playful | 75% serious | Money is serious. Occasional lightness in empty states only. |

### Terminology
| Preferred | Avoid | Reason |
|-----------|-------|--------|
| workspace | account, organization | We're a workspace, not a bank |
| team member | user, seat | People, not licenses |
| billing cycle | billing period, pay period | Consistency |
| revenue schedule | rev rec schedule | Clarity for non-accountants |
| connect | integrate, sync | Simpler verb |
| review | approve, sign off | Lower friction language |

### Writing Rules
1. **Lead with the action.** "Export your Q3 report" not "Your Q3 report is ready for export."
2. **Use specific numbers.** "$12,450 recognized this month" not "Revenue has been recognized."
3. **Name the object.** "3 invoices need review" not "3 items need attention."
4. **No jargon escalation.** If the user typed "billing," respond with "billing" — don't upgrade to "invoicing."
5. **Error messages explain what happened AND what to do.** Never just say what went wrong.
6. **Confirmations are one sentence.** "Invoice #4021 sent to acme@corp.com." Done.
7. **Empty states suggest the first action.** "No revenue schedules yet. Create one to start tracking recognition."
8. **Tooltips max 15 words.** If you need more, link to docs.
9. **Button labels are 1–3 words.** Verb + noun. "Export report," "Add rule," "Connect Stripe."
10. **Never use "please" in error messages.** It implies the system is asking a favor.

### Tone Shifts
| Context | Tone Adjustment |
|---------|----------------|
| Errors & failures | Direct, helpful, zero blame. "We couldn't process this payment" not "Payment processing failed." |
| Success & completion | Brief, warm. "Done. Invoice sent." |
| Onboarding | Encouraging, specific. Guide each step. |
| Destructive actions | Clear, serious. Name exactly what will be deleted. |
| Empty states | Helpful, action-oriented. Never just "Nothing here." |
| Loading states | Transparent. "Calculating Q3 revenue..." not "Loading..." |

## Product Taxonomy

### Core Objects
- **Workspace** — top-level container (one per company)
- **Customer** — a paying entity with one or more subscriptions
- **Subscription** — a recurring billing agreement
- **Invoice** — a billing document tied to a subscription or one-time charge
- **Revenue Schedule** — ASC 606 compliant recognition timeline
- **Report** — a generated financial summary (P&L, MRR waterfall, cohort)
- **Integration** — a connected external system (Stripe, QuickBooks, Salesforce)
- **Rule** — an automation trigger (e.g., "auto-send invoice when subscription renews")
- **Team Member** — a person with a role (Admin, Analyst, Viewer)

### Navigation Structure
```
Dashboard
├── Revenue Overview
├── MRR Waterfall
└── Quick Actions

Customers
├── Customer List
├── Customer Detail
│   ├── Subscriptions
│   ├── Invoices
│   └── Revenue Schedule
└── Import Customers

Billing
├── Invoices
├── Payment Methods
├── Tax Configuration
└── Billing Rules

Revenue
├── Recognition Dashboard
├── Schedules
├── Journal Entries
└── ASC 606 Compliance

Reports
├── Financial Statements
├── SaaS Metrics
├── Custom Reports
└── Scheduled Reports

Integrations
├── Connected Apps
├── API Keys
└── Webhooks

Settings
├── Workspace
├── Team
├── Billing & Plans
└── Security
```

## Platform Details
- **Web app** (React + TypeScript, no mobile app planned for v1)
- **Target browsers**: Chrome 90+, Firefox 88+, Safari 15+, Edge 90+
- **Accessibility target**: WCAG 2.1 AA
- **Supported locales**: en-US (v1), en-GB, de-DE, fr-FR (v2)
- **Character limits**: follow Material Design guidelines for component types
