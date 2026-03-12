---
title: Content Measurement and Analytics
domain: operations
tags: [analytics, measurement, metrics, roi, kpis, a-b-testing]
sources:
  - "Podmajersky, T. (2019). Strategic Writing for UX"
  - "Richards, S. (2017). Content Design"
  - "Google. HEART Framework for UX Metrics"
---

### Core Principle

Content that isn't measured is content that can't be improved. But not all metrics matter equally. Focus on metrics that reflect user success, not vanity metrics like page views.

### The HEART Framework (Google)

**Happiness** — User satisfaction with the content experience
- Survey scores (CSAT, NPS)
- Content helpfulness ratings ("Was this helpful? Yes/No")
- Sentiment in feedback

**Engagement** — Interaction with content
- Click-through rates on CTAs
- Feature adoption after content changes
- Time on page (lower can be better for task-oriented content)

**Adoption** — New users/features activated through content
- Onboarding completion rate
- Feature discovery rate after tooltip/guide introduction
- Account activation rate

**Retention** — Users returning after content interactions
- Return visit rate
- Churn rate changes after content improvements
- Notification engagement over time (are users muting?)

**Task Success** — Users completing their goals
- Task completion rate (the most important metric)
- Error rate during forms/flows
- Support ticket volume (lower = better content)
- Time to completion

### Key Metrics by Content Type

| Content type | Primary metric | Secondary metrics |
|-------------|---------------|-------------------|
| **Error messages** | Error recovery rate | Support tickets filed, task abandonment |
| **Onboarding** | Activation rate | Time to first value, completion rate |
| **CTAs** | Click-through rate | Conversion rate, bounce rate |
| **Forms** | Completion rate | Error rate, abandonment point |
| **Notifications** | Open rate + action rate | Mute/unsubscribe rate |
| **Empty states** | First action taken | Feature adoption, return rate |
| **Help content** | Task completion after reading | Support ticket deflection |
| **Tooltips** | Feature adoption | Tooltip dismissal rate |
| **Search** | Successful search rate | No-results rate, query refinement |

### A/B Testing Content

**What to test:**
- CTA text ("Get started" vs. "Try it free" vs. "Start your trial")
- Error message wording (technical vs. plain language)
- Onboarding flow copy (minimal vs. detailed)
- Notification frequency and wording
- Form label phrasing and help text

**How to test properly:**
1. **One variable at a time.** Change only the content, not the design.
2. **Sufficient sample size.** Use a calculator — don't declare winners too early.
3. **Statistical significance.** Target 95% confidence minimum.
4. **Run long enough.** At least 1-2 full business cycles (include weekdays and weekends).
5. **Measure what matters.** CTR is meaningless if conversion doesn't improve.

**Common content A/B tests:**
```
Test: "Submit" vs. "Create account" vs. "Get started free"
Metric: Sign-up conversion rate
Result: Specific, benefit-oriented CTAs typically win by 10-30%

Test: "Error: Invalid input" vs. "Enter a valid email address (e.g., name@example.com)"
Metric: Form completion rate after error
Result: Specific, example-driven errors reduce repeat errors by 20-40%
```

### Measuring Content ROI

**Direct impact:**
- CTA change → conversion rate change → revenue impact
- Error message improvement → reduced support tickets → cost savings
- Onboarding content change → activation rate → retention → LTV

**Calculating content value:**
```
Before: 1000 users × 45% completion = 450 conversions
After:  1000 users × 52% completion = 520 conversions
Lift:   70 additional conversions × $50 average value = $3,500/month
```

### Content Audit Metrics

When auditing existing content, measure:
1. **Readability score** — Flesch-Kincaid grade level
2. **Word count** — Is it within budget for the component?
3. **Voice consistency** — Does it match the brand voice guide?
4. **Terminology consistency** — Same words for same concepts everywhere?
5. **Accessibility compliance** — WCAG criteria met?
6. **Freshness** — When was this last reviewed? Is it still accurate?

### Building a Content Dashboard

**Track weekly:**
- Task completion rates for key flows
- Error recovery rates
- Support ticket volume by content-related topics
- CTA conversion rates

**Track monthly:**
- Content readability scores across the product
- A/B test results and learnings
- User feedback and helpfulness ratings
- Content coverage (are there pages/flows without proper content?)

**Track quarterly:**
- Content ROI by initiative
- Voice consistency audit results
- Accessibility compliance scores
- Content debt (outdated, inconsistent, or missing content)
