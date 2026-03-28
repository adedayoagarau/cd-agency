# Vaultline — Notifications

All notification copy across channels. Use with the Notification Writer agent.

---

## In-App Notifications

### Payment Received
```
Channel: In-app toast (bottom-right, auto-dismiss 5s)
Title: Payment received
Body: $2,499.00 from Acme Corp for Invoice #INV-4021.
Action: View Invoice
```

### Invoice Overdue
```
Channel: In-app banner (persistent, dismissible)
Title: Overdue invoice
Body: Invoice #INV-3987 for TechStart Inc. is 7 days past due ($899.00).
Action: Send Reminder | View Invoice
```

### Sync Complete
```
Channel: In-app toast
Title: Stripe sync complete
Body: 47 customers, 128 subscriptions, and 312 invoices imported.
Action: View Import Summary
```

### Sync Error
```
Channel: In-app banner (persistent)
Title: Sync paused
Body: 3 customer records have conflicts between Stripe and Vaultline. Resolve them to continue syncing.
Action: Resolve Conflicts
```

### Team Member Joined
```
Channel: In-app toast
Title: New team member
Body: jordan@acmecorp.com joined as an Analyst.
Action: View Team
```

### Report Ready
```
Channel: In-app toast
Title: Report ready
Body: Your Q1 2026 Revenue Summary is ready to view.
Action: Open Report
```

### Subscription Canceled
```
Channel: In-app notification center
Title: Subscription canceled
Body: TechStart Inc. canceled their Pro plan. Their subscription ends on April 30, 2026.
Action: View Customer
```

### Usage Limit Warning
```
Channel: In-app banner (persistent)
Title: Approaching plan limit
Body: You've used 450 of 500 included invoices this month. Upgrade to avoid overage charges.
Action: View Plans | Dismiss
```

---

## Email Notifications

### Welcome Email
```
Subject: Welcome to Vaultline — your workspace is ready
Preview text: Start by connecting your billing system

Hi Sarah,

Your Vaultline workspace "Acme Corp" is ready.

Here are three things to do first:

1. Connect Stripe to import your billing data
2. Invite your finance team
3. Set up your first MRR report

[Go to Your Workspace]

If you need help getting started, reply to this email or book a call with our team.

— The Vaultline Team
```

### Invoice Sent (to Vaultline user)
```
Subject: Invoice #INV-4021 sent to Acme Corp
Preview text: $2,499.00 — awaiting payment

Invoice #INV-4021 has been sent to billing@acmecorp.com.

Amount: $2,499.00
Due date: March 15, 2026
Customer: Acme Corp

[View Invoice]
```

### Payment Received
```
Subject: Payment received — $2,499.00 from Acme Corp
Preview text: Invoice #INV-4021 is now paid

Great news — Acme Corp paid Invoice #INV-4021.

Amount: $2,499.00
Payment method: Visa ending in 4242
Date: March 10, 2026

[View Payment Details]
```

### Overdue Reminder (to Vaultline user)
```
Subject: Invoice #INV-3987 is 7 days overdue
Preview text: $899.00 from TechStart Inc. — action needed

Invoice #INV-3987 for TechStart Inc. is now 7 days past due.

Amount: $899.00
Due date: March 1, 2026
Customer contact: billing@techstart.io

You can send a payment reminder directly from Vaultline:

[Send Reminder]  [View Invoice]

Tip: Set up automated reminders in Billing Rules to handle overdue invoices automatically.
```

### Weekly Summary
```
Subject: Your weekly revenue summary — Mar 3–9, 2026
Preview text: $47,200 collected this week

Here's your Vaultline weekly summary:

Revenue collected: $47,200.00 (+8% vs last week)
Invoices sent: 23
Invoices paid: 19
New customers: 4
Churned: 1

Top action items:
• 3 invoices are overdue (total: $4,297.00)
• 2 subscriptions are up for renewal this week
• 1 customer flagged as at-risk

[View Dashboard]
```

### Monthly Report Auto-Send
```
Subject: February 2026 MRR Report — Acme Corp
Preview text: MRR: $124,500 (+3.2%)

Your scheduled monthly report is ready.

MRR: $124,500 (+3.2% vs January)
New MRR: $8,400
Expansion MRR: $3,200
Churned MRR: -$4,100
Net new MRR: $7,500

[View Full Report]  [Download PDF]
```

---

## Push Notifications (future mobile app)

### Payment Received
```
Title: Payment received
Body: $2,499.00 from Acme Corp
```

### Invoice Overdue
```
Title: Invoice overdue
Body: #INV-3987 — TechStart Inc. — $899.00 (7 days)
```

### Subscription Canceled
```
Title: Subscription canceled
Body: TechStart Inc. canceled their Pro plan
```

### Sync Error
```
Title: Sync paused
Body: 3 conflicts need resolution
```

---

## Slack Integration Messages

### Payment Received
```
💰 *Payment received*
$2,499.00 from *Acme Corp* (Invoice #INV-4021)
<View in Vaultline|https://app.vaultline.com/invoices/INV-4021>
```

### Customer Churned
```
📉 *Customer churned*
*TechStart Inc.* canceled their Pro plan ($899/mo)
Subscription ends: April 30, 2026
<View customer|https://app.vaultline.com/customers/techstart>
```

### Weekly Summary
```
📊 *Weekly Revenue Summary* (Mar 3–9)
• Collected: $47,200 (+8%)
• Invoices sent: 23 | Paid: 19
• New customers: 4 | Churned: 1
• ⚠️ 3 overdue invoices ($4,297)
<Open dashboard|https://app.vaultline.com/dashboard>
```
