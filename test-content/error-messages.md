# Vaultline — Error Messages

Existing error messages that need rewriting. Use with the Error Message Architect agent.

---

## Authentication Errors

### Login Failed
```
Current: Invalid credentials. Please check your email and password and try again.
Context: User entered wrong email/password on login screen.
Severity: Low — common user error
```

### Session Expired
```
Current: Your session has expired due to inactivity. You have been logged out for security reasons. Please log in again to continue.
Context: User left tab open for 30+ minutes. They may have unsaved work.
Severity: Medium — could lose unsaved changes
```

### Account Locked
```
Current: Error: Account locked. Too many failed attempts. Try again in 30 minutes or reset your password.
Context: 5 failed login attempts in 10 minutes. Triggered for security.
Severity: Medium — user is blocked but it's for their protection
```

---

## Billing Errors

### Payment Failed
```
Current: Payment processing failed. Error code: CARD_DECLINED. Please update your payment method.
Context: Monthly subscription charge was declined by the card issuer.
Severity: High — service may be interrupted
```

### Invoice Generation Error
```
Current: We were unable to generate your invoice. An unexpected error occurred during invoice creation. Please try again or contact support if the issue persists. Error ID: err_inv_7x2k9m
Context: Tax calculation API timed out during invoice generation.
Severity: Medium — invoice not created but no data lost
```

### Subscription Downgrade Blocked
```
Current: Cannot downgrade. You currently have 12 team members but the Basic plan only supports 5. Remove team members before downgrading.
Context: User trying to switch from Pro (unlimited seats) to Basic (5 seats).
Severity: Low — informational blocker
```

---

## Integration Errors

### Stripe Connection Failed
```
Current: Failed to connect to Stripe. Please check your API keys and try again. If the problem persists, contact support.
Context: User entered an invalid Stripe API key during integration setup.
Severity: Low — just a bad key entry
```

### Sync Conflict
```
Current: Sync error: Conflict detected. Customer "Acme Corp" exists in both Stripe and Vaultline with different email addresses. Manual resolution required.
Context: Same customer has billing@acme.com in Stripe but finance@acme.com in Vaultline.
Severity: Medium — sync is paused for this record
```

### Webhook Delivery Failed
```
Current: Webhook delivery failed after 3 attempts. Endpoint https://api.partner.com/webhooks returned HTTP 503. Next retry in 1 hour.
Context: Partner's webhook endpoint is down. Events are queuing.
Severity: Low — automatic retry will handle it
```

---

## Data Errors

### Import Failed
```
Current: CSV import failed. Error on row 247: "subscription_start" field contains invalid date format "13/32/2025". Expected format: YYYY-MM-DD.
Context: User uploaded a CSV with a bad date in one row.
Severity: Low — can fix and re-upload
```

### Report Generation Timeout
```
Current: Report generation timed out. The requested date range contains too much data. Try a smaller date range or contact support for assistance.
Context: User requested a 3-year report with line-item detail. Query exceeded 30s timeout.
Severity: Low — no data lost, just need smaller scope
```

### Duplicate Customer
```
Current: Error: A customer with this email address already exists in your workspace. Duplicate customers are not allowed.
Context: User trying to create a customer but one already exists with that email.
Severity: Low — informational
```

---

## Permission Errors

### Forbidden Action
```
Current: Error 403: You do not have permission to perform this action. Contact your workspace administrator.
Context: Analyst-role user tried to delete an invoice (requires Admin role).
Severity: Low — expected behavior
```

### Read-Only Workspace
```
Current: This workspace is in read-only mode. Billing changes are disabled while your account is past due. Please update your payment method to restore full access.
Context: Workspace is past due on their Vaultline subscription.
Severity: High — blocks all write operations
```

---

## System Errors

### Service Unavailable
```
Current: Service temporarily unavailable. We're experiencing high demand. Please try again in a few minutes.
Context: System is under heavy load during end-of-month billing runs.
Severity: Medium — temporary but blocks work
```

### Data Export Failed
```
Current: Export failed. An error occurred while generating your export file. Please try again. If the problem continues, contact support at help@vaultline.com.
Context: PDF generation service crashed mid-export.
Severity: Low — can retry
```
