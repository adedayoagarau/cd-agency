export interface HistoryRun {
  id: string;
  agent: string;
  agentSlug: string;
  input: string;
  output: string;
  status: "passed" | "iterating" | "failed";
  score: number | null;
  model: string;
  duration: string;
  time: string;
  iterations?: number;
  evaluation?: {
    readability: number;
    linter: number;
    accessibility: number;
    voice: number;
  };
}

export const historyRuns: HistoryRun[] = [
  { id: "r1", agent: "Microcopy Writer", agentSlug: "microcopy-writer", input: "Write a button label for file upload in the settings panel", output: "Choose file \u2192 Upload", status: "passed", score: 0.91, model: "Claude 3.5 Sonnet", duration: "2.3s", time: "2 min ago", iterations: 1, evaluation: { readability: 0.88, linter: 0.96, accessibility: 0.85, voice: 0.94 } },
  { id: "r2", agent: "Brand Voice Evaluator", agentSlug: "brand-voice-evaluator", input: "Evaluate: 'Your account has been successfully created! Welcome aboard!'", output: "Score: 72/100. Issues: exclamation mark in confirmation, 'aboard' is too casual for brand voice.", status: "passed", score: 0.87, model: "Claude 3.5 Sonnet", duration: "3.1s", time: "14 min ago", evaluation: { readability: 0.92, linter: 0.81, accessibility: 0.90, voice: 0.85 } },
  { id: "r3", agent: "Error Message Crafter", agentSlug: "error-message-crafter", input: "Rewrite: 'Error 403: Forbidden. Access denied.'", output: "You don't have permission to view this page. Contact your team admin for access.", status: "passed", score: 0.93, model: "Claude 3.5 Sonnet", duration: "1.8s", time: "1 hour ago", iterations: 2, evaluation: { readability: 0.95, linter: 0.94, accessibility: 0.88, voice: 0.96 } },
  { id: "r4", agent: "SEO Meta Generator", agentSlug: "seo-meta-generator", input: "Generate meta for the pricing page", output: "Title: Pricing Plans \u2014 Start Free, Scale as You Grow | Acme\nDescription: Choose from Free, Pro, or Enterprise plans...", status: "passed", score: 0.78, model: "GPT-4o", duration: "4.2s", time: "3 hours ago", evaluation: { readability: 0.82, linter: 0.76, accessibility: 0.74, voice: 0.80 } },
  { id: "r5", agent: "Tone Adjuster (Formal)", agentSlug: "tone-adjuster-formal", input: "Make formal: 'Hey! Check out our cool new feature that lets you do stuff way faster'", output: "Introducing our latest enhancement: a streamlined workflow designed to improve your productivity.", status: "passed", score: 0.90, model: "Claude 3.5 Sonnet", duration: "2.7s", time: "5 hours ago", evaluation: { readability: 0.86, linter: 0.92, accessibility: 0.88, voice: 0.94 } },
  { id: "r6", agent: "Microcopy Writer", agentSlug: "microcopy-writer", input: "Write empty state for the notifications inbox", output: "All caught up! No new notifications.", status: "iterating", score: null, model: "Claude 3.5 Sonnet", duration: "\u2014", time: "Just now", iterations: 2 },
  { id: "r7", agent: "Accessibility Checker", agentSlug: "accessibility-checker", input: "Check: 'Click the red button to delete your account permanently'", output: "Issues found: color-only reference ('red button'), no confirmation step mentioned, anxiety-inducing language.", status: "passed", score: 0.92, model: "Claude 3.5 Sonnet", duration: "2.1s", time: "6 hours ago", evaluation: { readability: 0.94, linter: 0.90, accessibility: 0.95, voice: 0.88 } },
  { id: "r8", agent: "Content Localizer", agentSlug: "content-localizer", input: "Localize for DE market: 'Sign up for free and start building'", output: "Kostenlos registrieren und direkt loslegen", status: "passed", score: 0.81, model: "GPT-4o", duration: "5.4s", time: "Yesterday", evaluation: { readability: 0.78, linter: 0.84, accessibility: 0.80, voice: 0.82 } },
  { id: "r9", agent: "Notification Writer", agentSlug: "notification-writer", input: "Write push notification for abandoned cart", output: "Your items are waiting \u2014 complete your order before they sell out.", status: "passed", score: 0.89, model: "Claude 3.5 Sonnet", duration: "1.9s", time: "Yesterday", evaluation: { readability: 0.91, linter: 0.88, accessibility: 0.86, voice: 0.92 } },
  { id: "r10", agent: "Brand Voice Evaluator", agentSlug: "brand-voice-evaluator", input: "Evaluate homepage hero copy", output: "Failed quality gate. Voice consistency below threshold.", status: "failed", score: 0.52, model: "Claude 3.5 Sonnet", duration: "3.8s", time: "2 days ago", evaluation: { readability: 0.60, linter: 0.48, accessibility: 0.55, voice: 0.45 } },
  { id: "r11", agent: "Help Doc Writer", agentSlug: "help-doc-writer", input: "Write troubleshooting guide for connector sync failures", output: "# Fixing Connector Sync Issues\n\n1. Check your API key...", status: "passed", score: 0.87, model: "Claude 3.5 Sonnet", duration: "6.2s", time: "2 days ago", evaluation: { readability: 0.89, linter: 0.86, accessibility: 0.84, voice: 0.88 } },
  { id: "r12", agent: "Changelog Writer", agentSlug: "changelog-writer", input: "Write release notes for v2.3", output: "## What's new in v2.3\n- Faster agent runs...", status: "passed", score: 0.84, model: "GPT-4o", duration: "4.8s", time: "3 days ago", evaluation: { readability: 0.86, linter: 0.82, accessibility: 0.80, voice: 0.88 } },
  { id: "r13", agent: "Microcopy Writer", agentSlug: "microcopy-writer", input: "Write tooltip for the analytics dashboard info icon", output: "See how your content performs across channels and time periods.", status: "passed", score: 0.91, model: "Claude 3.5 Sonnet", duration: "1.5s", time: "3 days ago", evaluation: { readability: 0.93, linter: 0.90, accessibility: 0.88, voice: 0.92 } },
  { id: "r14", agent: "Error Message Crafter", agentSlug: "error-message-crafter", input: "Rewrite: 'Invalid input. Please try again.'", output: "That doesn't look right. Check the format and try again.", status: "failed", score: 0.58, model: "Claude 3.5 Sonnet", duration: "2.0s", time: "4 days ago", evaluation: { readability: 0.72, linter: 0.55, accessibility: 0.50, voice: 0.54 } },
  { id: "r15", agent: "Onboarding Flow Writer", agentSlug: "onboarding-flow-writer", input: "Write welcome screen copy for new users", output: "Welcome to Acme \u2014 let's get you set up in 2 minutes.", status: "passed", score: 0.86, model: "Claude 3.5 Sonnet", duration: "3.3s", time: "5 days ago", evaluation: { readability: 0.88, linter: 0.84, accessibility: 0.82, voice: 0.90 } },
];
