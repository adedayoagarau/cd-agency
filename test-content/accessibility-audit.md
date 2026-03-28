# Vaultline — Accessibility Audit Content

Content samples with known accessibility issues for testing the Accessibility Checker agent and a11y scoring.

---

## Known Good Examples (should pass)

### Accessible Error Message
```
We couldn't process your payment. Your card ending in 4242 was declined. Update your payment method to continue using Vaultline.

[Update Payment Method]
```

### Accessible Empty State
```
No invoices yet. Create your first invoice to start billing customers.

[Create Invoice]
```

### Accessible Status Update
```
Import complete. 1,247 customers and 893 subscriptions added to your workspace.

[View Import Summary]
```

### Accessible Form Field
```
Label: Email address
Placeholder: sarah@company.com
Helper text: We'll send a verification email to this address.
Error: Enter a valid email address (e.g., name@company.com).
```

---

## Known Bad Examples (should fail a11y checks)

### Color-Only Information
```
Fields marked in red are required. Green fields have been validated successfully.
```
**Issue**: Relies on color alone to convey meaning (WCAG 1.4.1)

### Missing Alt-Text Instructions
```
See the diagram below for the revenue recognition workflow. The flowchart shows how invoices move through the system.
```
**Issue**: References visual content without describing it (WCAG 1.1.1)

### Directional References
```
Click the button on the right to save your changes. Use the menu on the left to navigate between sections.
```
**Issue**: Relies on spatial/visual layout (WCAG 1.3.3)

### Complex Language
```
Pursuant to ASC 606-10-25-27, the transaction price shall be allocated to each performance obligation identified in the contract on a relative standalone selling price basis, utilizing the residual approach when the standalone selling price is highly variable or uncertain.
```
**Issue**: Reading level too high for general users (WCAG 3.1.5)

### Ambiguous Link Text
```
For more information about our pricing, click here. To learn about integrations, click here. For the API documentation, click here.
```
**Issue**: Non-descriptive link text (WCAG 2.4.4)

### Flashing/Animation Reference
```
Watch the pulsing notification badge for new alerts. The flashing banner indicates urgent action is needed.
```
**Issue**: References potentially harmful visual effects (WCAG 2.3.1)

### Time-Dependent Instructions
```
Complete this form within 5 minutes or your session will expire and all data will be lost. The countdown timer is shown in the top-right corner.
```
**Issue**: Time limit without option to extend (WCAG 2.2.1)

### ALL CAPS
```
WARNING: DELETING YOUR WORKSPACE WILL PERMANENTLY REMOVE ALL DATA INCLUDING CUSTOMERS, INVOICES, AND REVENUE SCHEDULES. THIS ACTION CANNOT BE UNDONE.
```
**Issue**: All caps reduces readability, appears as shouting (readability concern)

---

## Mixed Quality Content (realistic audit)

### Invoice Email — Current Version
```
Subject: Invoice #INV-4021

Dear Customer,

Please find attached your invoice for the amount of $2,499.00. Payment is due within 30 days of receipt. If you have any questions regarding this invoice, please do not hesitate to contact our billing department.

Click here to view your invoice online. See below for payment instructions. The blue button will take you to our payment portal.

Thank you for your continued business.

Regards,
The Vaultline Team
```
**Issues**:
- "Click here" — non-descriptive link text
- "See below" — directional reference
- "The blue button" — color-only reference
- "Dear Customer" — impersonal
- Passive voice throughout
- "Please do not hesitate" — wordy

### Dashboard Tooltip — Current Version
```
This chart displays your MRR over the past 12 months. Hover over the bars to see monthly values. The green bars indicate growth months and red bars indicate decline. Use the legend at the bottom to toggle data series on/off.
```
**Issues**:
- "Hover over" — not accessible for keyboard/touch users
- Color-only references (green/red)
- "At the bottom" — directional reference
- Tooltip is too long (>15 words per Vaultline style guide)

### Onboarding Step — Current Version
```
Almost done! Just a few more steps and you'll be all set. Click the colorful icons below to choose your preferred dashboard layout. The selected option will be highlighted in blue.

⏱ You have 10 minutes to complete setup before your session expires.
```
**Issues**:
- "Click" — not inclusive of keyboard/voice users
- "Colorful icons" — relies on visual appearance
- "Below" — directional reference
- "Highlighted in blue" — color-only reference
- Session timeout without extension option

---

## Accessible Alternatives (rewritten versions)

### Invoice Email — Accessible Version
```
Subject: Invoice #INV-4021 — $2,499.00 due March 15

Hi Sarah,

Invoice #INV-4021 for $2,499.00 is ready. Payment is due by March 15, 2026.

View and pay Invoice #INV-4021: [link]

Line items:
• Pro Plan (Monthly): $1,999.00
• Additional seats (5): $500.00

Questions? Reply to this email or contact billing@vaultline.com.

— Vaultline
```

### Dashboard Tooltip — Accessible Version
```
Monthly Recurring Revenue for the past 12 months. Select any month to see details.
```

### Onboarding Step — Accessible Version
```
Choose your dashboard layout

Select the layout that works best for your workflow. You can change this anytime in Settings.

○ Overview — Key metrics and recent activity
○ Detailed — All metrics with drill-down charts
○ Compact — Minimal view with quick actions
```
