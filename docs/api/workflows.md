# Built-in Workflows

> Stability: Stable

CD Agency ships with 6 pre-built multi-agent workflows.

## Content Audit

**Slug:** `content-audit`
**Steps:** 4
**Agents:** Generalist → Tone → Accessibility → Microcopy

Comprehensive content quality audit. The Generalist scans for overall issues,
the Tone Evaluator checks voice, the Accessibility Auditor flags a11y issues,
and the Microcopy Reviewer polishes the final output.

```bash
cd-agency workflow run content-audit \
  -F "content=Welcome to our app! Click here to get started." \
  -F "brand_guidelines=Friendly and professional" \
  -F "target_audience=New users"
```

**Input fields:** `content`, `brand_guidelines`, `target_audience`,
`target_tone`, `channel`, `content_type`, `ui_context`

---

## Error Message Pipeline

**Slug:** `error-message-pipeline`
**Steps:** 4
**Agents:** Error Architect → Tone → Accessibility → Microcopy

End-to-end error message creation from scenario to polished copy.

```bash
cd-agency workflow run error-message-pipeline \
  -F "error_scenario=Payment card declined" \
  -F "severity=warning" \
  -F "target_audience=Non-technical consumers"
```

**Input fields:** `error_scenario`, `severity`, `target_audience`,
`brand_guidelines`, `target_tone`

---

## Launch Content Package

**Slug:** `launch-content-package`
**Steps:** 4
**Agents:** Onboarding → CTA → Notification → Microcopy

Complete content package for a product launch — onboarding flow, CTAs,
notification suite, and final polish.

```bash
cd-agency workflow run launch-content-package \
  -F "product_description=A new project management tool for small teams" \
  -F "target_audience=Small business owners"
```

**Input fields:** `product_description`, `target_audience`, `brand_guidelines`,
`key_features`

---

## Localization Prep

**Slug:** `localization-prep`
**Steps:** 3
**Agents:** Localization Strategist → Accessibility → Generalist

Prepare content for global deployment. Audit for i18n issues, check
accessibility across locales, and polish.

```bash
cd-agency workflow run localization-prep \
  -F "content=Your trial expires in 3 days. Upgrade now!" \
  -F "target_locales=ja,de,es,pt-BR"
```

**Input fields:** `content`, `target_locales`, `brand_guidelines`

---

## Notification Suite

**Slug:** `notification-suite`
**Steps:** 4
**Agents:** Notification Designer → Mobile Writer → Tone → Microcopy

Complete notification content across channels — push, email, in-app, and SMS.

```bash
cd-agency workflow run notification-suite \
  -F "notification_context=User has items in cart for 24 hours" \
  -F "channels=push,email,in-app"
```

**Input fields:** `notification_context`, `channels`, `brand_guidelines`,
`urgency`

---

## Content Quality Pipeline

**Slug:** `content-quality-pipeline`
**Steps:** 5
**Agents:** Generalist → Consistency Checker → Tone + Accessibility (parallel) → Microcopy

End-to-end content quality gate. The Generalist rewrites, the Consistency
Checker audits terminology and patterns, Tone and Accessibility run in parallel,
and Microcopy polishes the final output.

```bash
cd-agency workflow run content-quality-pipeline \
  -F "content=Welcome to your new workspace! Click here to get started." \
  -F "brand_guidelines=Friendly, professional, sentence case" \
  -F "target_audience=New users"
```

**Input fields:** `content`, `brand_guidelines`, `target_audience`,
`existing_terms`, `product_area`, `target_tone`, `channel`, `content_type`,
`ui_context`
