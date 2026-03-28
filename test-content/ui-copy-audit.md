# Vaultline — UI Copy Audit

Content from the live product that needs review. Each section is a screen or component.

---

## Dashboard

### Greeting
```
Welcome back, Sarah! Here's your financial overview for today.
```

### Revenue Card
```
Title: Total Revenue
Value: $847,231.00
Subtitle: ↑ 12.3% vs last month
```

### MRR Card
```
Title: Monthly Recurring Revenue
Value: $124,500
Subtitle: 847 active subscriptions
```

### Quick Actions
```
- Create Invoice
- Add Customer
- Run Report
- View Integrations
```

### Alert Banner
```
⚠️ 3 invoices are overdue. Click here to review them.
```

---

## Customer List

### Page Header
```
Customers (2,847)
Manage your customer accounts, subscriptions, and billing relationships.
```

### Search Placeholder
```
Search by name, email, or customer ID...
```

### Empty State (filtered)
```
No customers match your filters.
Try adjusting your search criteria or clearing filters to see all customers.
```

### Table Headers
```
Customer | Plan | MRR | Status | Last Invoice | Actions
```

### Status Badges
```
Active | Churned | Trial | Past Due | Paused
```

---

## Invoice Detail

### Page Title
```
Invoice #INV-4021
```

### Status
```
Status: Sent — Awaiting payment
Due date: March 15, 2026
Amount: $2,499.00
```

### Line Items Table
```
Description          | Qty | Unit Price | Amount
Pro Plan (Monthly)   | 1   | $1,999.00  | $1,999.00
Additional seats (5) | 5   | $100.00    | $500.00
                              Subtotal:    $2,499.00
                              Tax (0%):    $0.00
                              Total:       $2,499.00
```

### Action Buttons
```
[Send Reminder]  [Mark as Paid]  [Download PDF]  [Void Invoice]
```

### Payment Timeline
```
Feb 15 — Invoice created by Sarah L.
Feb 15 — Invoice sent to billing@acmecorp.com
Feb 22 — Payment reminder sent (automated)
Mar 1  — Second reminder sent (automated)
```

---

## Billing Rules

### Page Description
```
Automate your billing workflows. Rules trigger actions when specific conditions are met, so you don't have to do repetitive tasks manually.
```

### Rule Card
```
Title: Auto-send on renewal
Description: Automatically send invoices when a subscription renews. Invoices are generated 3 days before the renewal date and sent immediately.
Status: Active
Last triggered: 2 hours ago (Invoice #INV-4019)
```

### Create Rule Modal
```
Title: Create billing rule

Trigger: [When a subscription renews ▾]
Action: [Send invoice automatically ▾]
Timing: [3] days before renewal

Additional options:
☑ Include payment link in invoice
☑ Send copy to workspace admins
☐ Apply late fee after grace period

[Cancel]  [Create Rule]
```

---

## Settings — Workspace

### Section: General
```
Workspace name: Acme Corp
Workspace ID: ws_acme_7x9k2m
Created: January 12, 2025
```

### Section: Danger Zone
```
Delete workspace

This will permanently delete your workspace, including all customers, invoices, revenue schedules, integrations, and team member access. This action cannot be undone.

Type "Acme Corp" to confirm deletion.

[input field]

[Delete Acme Corp]
```

---

## Integration Setup — Stripe

### Step 1
```
Connect Stripe
Link your Stripe account to automatically sync customers, subscriptions, and payment data.

What we'll import:
• Customer profiles and metadata
• Active and canceled subscriptions
• Payment history (last 12 months)
• Product and price catalogs

[Connect with Stripe]
```

### Step 2
```
Choose what to sync

Select the data you want to keep in sync between Stripe and Vaultline.

☑ Customers — Import and sync customer profiles
☑ Subscriptions — Track subscription lifecycle events
☑ Invoices — Mirror Stripe invoices in Vaultline
☐ Payment methods — Store tokenized payment references
☑ Products & prices — Sync your product catalog

Sync direction: [Stripe → Vaultline (one-way) ▾]

[Back]  [Start Import]
```

### Step 3 — Progress
```
Importing from Stripe...

Customers:     1,247 of 1,247 ✓
Subscriptions: 893 of 1,102 ◌
Invoices:      Waiting...
Products:      Waiting...

Estimated time remaining: ~4 minutes

[Cancel Import]
```

---

## Reports

### Empty State
```
No reports yet

Create your first report to get insights into your revenue, churn, and growth metrics. We'll help you set up the metrics that matter most.

Popular templates:
• MRR Waterfall — Track expansion, contraction, and churn
• Revenue by Cohort — See how customer groups perform over time
• P&L Summary — Monthly profit and loss overview

[Create Report]  [Browse Templates]
```

### Report Builder
```
Title: Q1 2026 Revenue Summary
Type: Financial Statement
Period: Jan 1, 2026 — Mar 31, 2026
Format: PDF with charts

Include:
☑ Revenue breakdown by product
☑ MRR waterfall chart
☑ Customer acquisition cost
☐ Detailed line items
☑ Year-over-year comparison

[Cancel]  [Generate Report]
```

---

## Problematic Copy (for testing linter/scoring)

### Bad Error Messages
```
Error: Something went wrong. Please try again later.
```

```
Error 500: Internal Server Error. Contact support.
```

```
Oops! We couldn't do that. Please try again or contact us if the problem persists.
```

### Bad Button Labels
```
[Click Here]
[Submit]
[OK]
[Yes]
[Proceed to the Next Step]
```

### Bad Empty States
```
Nothing to show.
```

```
No data available at this time.
```

```
Empty.
```

### Jargon-Heavy Copy
```
Utilize the webhook endpoint to programmatically interface with the billing subsystem and retrieve the canonical invoice payload for downstream reconciliation workflows.
```

### Passive Voice
```
Your invoice has been sent by the system. The payment will be processed within 3-5 business days. You will be notified when the transaction has been completed.
```

### Accessibility Issues
```
Click the red button to delete. Press the green button to save.
```

```
See the chart below for details. Refer to the image on the right for instructions.
```

```
Important information is highlighted in yellow.
```
