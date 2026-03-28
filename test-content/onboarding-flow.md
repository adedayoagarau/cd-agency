# Vaultline — Onboarding Flow

Complete onboarding sequence for new workspace creation. Use with Validation (check character limits per element type) and Scoring.

---

## Step 1: Welcome

### Headline
```
Welcome to Vaultline
```

### Subheadline
```
The financial operations platform built for SaaS teams. Set up your workspace in about 5 minutes.
```

### Body
```
We'll walk you through connecting your billing system, importing your customers, and setting up your first revenue report. You can skip any step and come back to it later.
```

### CTA Button
```
Get Started
```

### Skip Link
```
I'll set up later → Go to dashboard
```

---

## Step 2: Create Workspace

### Headline
```
Name your workspace
```

### Body
```
This is your team's shared space for managing billing, revenue, and financial reporting. You can change the name anytime in Settings.
```

### Field: Workspace Name
```
Label: Workspace name
Placeholder: e.g., Acme Corp
Helper text: Usually your company name.
Error (empty): Enter a workspace name to continue.
Error (taken): This name is already in use. Try a different name.
Error (too long): Workspace names can't exceed 50 characters.
```

### Field: Workspace URL
```
Label: Workspace URL
Prefix: app.vaultline.com/
Placeholder: acme-corp
Helper text: Letters, numbers, and hyphens only. This can't be changed later.
Error (taken): This URL is already taken. Try adding a number or abbreviation.
Error (invalid): Only letters, numbers, and hyphens are allowed.
```

### CTA
```
Create Workspace
```

---

## Step 3: Invite Team

### Headline
```
Invite your team
```

### Body
```
Add the people who'll be working with billing and revenue data. You can always invite more team members later.
```

### Role Descriptions
```
Admin — Full access to all features, settings, and team management.
Analyst — View and create reports, manage customers. Can't change settings or invite members.
Viewer — Read-only access to dashboards and reports. Can't modify any data.
```

### Email Input
```
Label: Email addresses
Placeholder: Enter emails, separated by commas
Helper text: We'll send each person an invite with instructions to join.
```

### Role Selector
```
Label: Role for all invitees
Options: Admin | Analyst | Viewer
```

### CTA
```
Send Invites
```

### Skip
```
Skip — I'll invite people later
```

---

## Step 4: Connect Billing

### Headline
```
Connect your billing system
```

### Body
```
Link your payment processor to automatically import customers, subscriptions, and invoices. This usually takes about 2 minutes.
```

### Integration Cards

#### Stripe
```
Title: Stripe
Description: Import customers, subscriptions, invoices, and payment data.
Badge: Most popular
CTA: Connect Stripe
```

#### QuickBooks
```
Title: QuickBooks
Description: Sync invoices, payments, and chart of accounts.
CTA: Connect QuickBooks
```

#### Manual Import
```
Title: CSV Import
Description: Upload customer and subscription data from a spreadsheet.
CTA: Upload CSV
```

### Skip
```
Skip — I'll connect later
```

### Help Text
```
Don't see your billing system? We're adding new integrations regularly. Contact us to request one.
```

---

## Step 5: First Report

### Headline
```
Create your first report
```

### Body
```
Choose a template to see your financial data in action. You can customize everything later.
```

### Template Cards

#### MRR Waterfall
```
Title: MRR Waterfall
Description: See how your monthly recurring revenue changes — new business, expansion, contraction, and churn in one view.
Badge: Recommended
CTA: Use This Template
```

#### Revenue Summary
```
Title: Revenue Summary
Description: Monthly revenue breakdown by product, plan, and customer segment.
CTA: Use This Template
```

#### Customer Health
```
Title: Customer Health
Description: Track at-risk customers based on usage patterns, payment behavior, and engagement signals.
CTA: Use This Template
```

### Skip
```
Skip — I'll explore on my own
```

---

## Step 6: Done

### Headline
```
You're all set
```

### Body
```
Your workspace is ready. Here are a few things to explore first:
```

### Checklist
```
☐ Review your imported data in Customers
☐ Set up a billing rule to automate invoice sending
☐ Schedule a weekly MRR report for your team
☐ Configure revenue recognition schedules
```

### CTA
```
Go to Dashboard
```

### Help
```
Need help getting started? Book a 15-minute setup call with our team.
[Book a Call]
```

---

## Onboarding Tooltips (in-app)

### First Dashboard Visit
```
This is your revenue overview. It updates in real-time as payments come in. Click any metric to drill down.
[Got it]
```

### First Customer View
```
Customer profiles show all their subscriptions, invoices, and payment history in one place. Try clicking a customer to see their details.
[Got it]  [Show me more]
```

### First Invoice Creation
```
Invoices can be sent manually or generated automatically with billing rules. We'll walk you through creating your first one.
[Start Tour]  [Skip]
```

---

## Progress Indicator Text
```
Step 1 of 6: Welcome
Step 2 of 6: Create workspace
Step 3 of 6: Invite team
Step 4 of 6: Connect billing
Step 5 of 6: First report
Step 6 of 6: You're all set
```
