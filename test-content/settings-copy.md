# Vaultline — Settings & Microcopy

All labels, helper text, tooltips, and microcopy from the Settings area. Use with the Microcopy Review agent.

---

## Workspace Settings

### General

```
Section: General
Description: Basic workspace configuration.

Field: Workspace name
Value: Acme Corp
Helper: The name shown across your workspace and in team invites.

Field: Workspace URL
Value: app.vaultline.com/acme-corp
Helper: This URL can't be changed after creation.
Badge: Locked

Field: Timezone
Value: America/New_York (EST)
Helper: Used for report dates, invoice due dates, and scheduled automations.

Field: Default currency
Value: USD ($)
Helper: The primary currency for invoices and reports. Multi-currency support is available on the Enterprise plan.

Field: Fiscal year start
Value: January
Helper: Affects quarterly breakdowns in reports and revenue recognition.
```

### Billing & Plans

```
Section: Your Plan
Current: Pro ($49/month)
Usage: 312 of 500 invoices this cycle
Renewal: Renews April 1, 2026

Button: [Change Plan]
Button: [View Invoice History]
Link: Cancel subscription

Upgrade banner:
Need more? Enterprise includes unlimited invoices, custom integrations, SSO, and dedicated support.
[Talk to Sales]
```

### Team Management

```
Section: Team Members (7)
Description: Manage who has access to this workspace and what they can do.

Button: [Invite Members]

Table headers: Name | Email | Role | Last Active | Actions

Role descriptions:
Admin — Full access. Can manage team, billing, and all workspace settings.
Analyst — Can view and create reports, manage customers, and handle invoices. Can't access settings or team management.
Viewer — Read-only access to dashboards and reports.

Actions dropdown: Change role | Remove from workspace

Confirmation: Remove team member
Body: Remove jordan@acmecorp.com from this workspace? They'll lose access immediately but their activity history will be preserved.
Buttons: [Cancel] [Remove Member]
```

### Security

```
Section: Security Settings

Toggle: Two-factor authentication
Status: Enabled for 5 of 7 team members
Helper: Require all team members to use 2FA. Members without 2FA will be prompted on their next login.
Button: [Enforce for All Members]

Toggle: Session timeout
Value: 30 minutes
Helper: Automatically sign out inactive team members after this duration.
Options: 15 minutes | 30 minutes | 1 hour | 4 hours | Never

Section: Login History
Description: Recent sign-ins to your workspace.
Table: Team Member | Date | IP Address | Location | Device
Link: View full audit log

Section: API Keys
Description: Manage API keys for programmatic access to Vaultline.
Helper: API keys have full access to your workspace data. Keep them secure and rotate them regularly.
Button: [Generate New Key]

API Key row:
Name: Production Key
Created: Feb 1, 2026
Last used: 2 hours ago
Actions: [Regenerate] [Delete]

Delete confirmation:
Title: Delete API key
Body: Delete "Production Key"? Any integrations using this key will stop working immediately.
Buttons: [Cancel] [Delete Key]
```

### Notifications

```
Section: Notification Preferences
Description: Choose which events trigger notifications and how you receive them.

Category: Payments
☑ Payment received — In-app, Email
☑ Payment failed — In-app, Email, Slack
☐ Payment refunded — In-app

Category: Invoices
☑ Invoice sent — In-app
☑ Invoice overdue — In-app, Email, Slack
☐ Invoice voided — In-app

Category: Customers
☑ New customer — In-app
☑ Customer churned — In-app, Email, Slack
☐ Subscription changed — In-app

Category: System
☑ Sync errors — In-app, Email
☑ Usage limits — In-app, Email
☐ Scheduled reports — Email

Button: [Save Preferences]
Success toast: Notification preferences saved.
```

---

## Tooltips (? icons throughout the app)

### Dashboard
```
MRR: Monthly Recurring Revenue — the total predictable revenue from all active subscriptions, normalized to a monthly amount.

ARR: Annual Recurring Revenue — MRR multiplied by 12.

Net Revenue Retention: The percentage of revenue retained from existing customers, including expansion and contraction. Above 100% means you're growing from existing customers.

Churn Rate: The percentage of customers or revenue lost in a given period.
```

### Billing
```
Grace period: The number of days after a failed payment before the subscription is canceled. During this time, we'll retry the payment automatically.

Proration: When a customer changes plans mid-cycle, proration adjusts the next invoice to account for the difference.

Tax configuration: Set up tax rates by region. Vaultline calculates tax automatically based on your customer's billing address.
```

### Revenue
```
ASC 606: The accounting standard for revenue recognition. Vaultline automates compliance by matching revenue to performance obligations.

Deferred revenue: Money received for services not yet delivered. Recognized as revenue over the service period.

Journal entry: An accounting record that moves amounts between accounts. Vaultline generates these automatically from your revenue schedules.
```

---

## Confirmation Dialogs

### Void Invoice
```
Title: Void invoice
Body: Void Invoice #INV-4021 ($2,499.00)? This removes it from the customer's outstanding balance. Voided invoices can't be reinstated — you'll need to create a new one.
Buttons: [Cancel] [Void Invoice]
```

### Delete Customer
```
Title: Delete customer
Body: Delete "Acme Corp" and all associated data? This removes 12 subscriptions, 47 invoices, and 3 revenue schedules. This action can't be undone.
Input: Type "Acme Corp" to confirm
Buttons: [Cancel] [Delete Customer]
```

### Cancel Subscription
```
Title: Cancel subscription
Body: Cancel the Pro plan for TechStart Inc.? They'll retain access until their current billing cycle ends on April 30, 2026. You can reactivate before then.
Options:
○ Cancel at end of cycle (April 30, 2026)
○ Cancel immediately — issue prorated refund of $449.50
Buttons: [Keep Subscription] [Cancel Subscription]
```

### Export Data
```
Title: Export workspace data
Body: Export all customers, invoices, and revenue data as a CSV file. This may take a few minutes for large workspaces.
Options:
☑ Customers (2,847 records)
☑ Invoices (8,421 records)
☑ Revenue schedules (1,203 records)
☐ Team activity log (12,847 records)
Buttons: [Cancel] [Start Export]
```
