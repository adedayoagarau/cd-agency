export type AgentCategory = "writing" | "evaluation" | "optimization" | "translation";

export interface Agent {
  slug: string;
  name: string;
  description: string;
  category: AgentCategory;
  model: string;
  tools: string[];
  qualityThreshold: number;
  avgScore: number;
  totalRuns: number;
  lastUsed: string | null;
}

export const agents: Agent[] = [
  {
    slug: "microcopy-writer",
    name: "Microcopy Writer",
    description: "Writes clear, concise UI microcopy — button labels, tooltips, empty states, confirmation dialogs, and inline help text.",
    category: "writing",
    model: "Claude 3.5 Sonnet",
    tools: ["RunLinter", "ScoreReadability", "CheckAccessibility", "RecallBrandVoice"],
    qualityThreshold: 0.75,
    avgScore: 0.91,
    totalRuns: 127,
    lastUsed: "2 hours ago",
  },
  {
    slug: "brand-voice-evaluator",
    name: "Brand Voice Evaluator",
    description: "Evaluates content against your brand's voice patterns, terminology rules, and style guidelines. Flags inconsistencies and suggests fixes.",
    category: "evaluation",
    model: "Claude 3.5 Sonnet",
    tools: ["RecallBrandVoice", "CheckVoiceConsistency", "ExtractBrandPatterns", "ScoreReadability"],
    qualityThreshold: 0.80,
    avgScore: 0.87,
    totalRuns: 89,
    lastUsed: "2 min ago",
  },
  {
    slug: "seo-meta-generator",
    name: "SEO Meta Generator",
    description: "Generates optimized meta titles, descriptions, and Open Graph tags that balance search performance with brand voice.",
    category: "optimization",
    model: "GPT-4o",
    tools: ["RunLinter", "ScoreReadability", "RecallBrandVoice"],
    qualityThreshold: 0.70,
    avgScore: 0.78,
    totalRuns: 64,
    lastUsed: "3 hours ago",
  },
  {
    slug: "error-message-crafter",
    name: "Error Message Crafter",
    description: "Rewrites error messages to be helpful, human, and actionable. Turns technical jargon into clear guidance.",
    category: "writing",
    model: "Claude 3.5 Sonnet",
    tools: ["RunLinter", "ScoreReadability", "CheckAccessibility", "RecallBrandVoice"],
    qualityThreshold: 0.80,
    avgScore: 0.93,
    totalRuns: 52,
    lastUsed: "1 hour ago",
  },
  {
    slug: "tone-adjuster-formal",
    name: "Tone Adjuster (Formal)",
    description: "Transforms casual or inconsistent copy into a polished, professional tone while preserving the original meaning.",
    category: "optimization",
    model: "Claude 3.5 Sonnet",
    tools: ["RecallBrandVoice", "CheckVoiceConsistency", "ScoreReadability"],
    qualityThreshold: 0.75,
    avgScore: 0.90,
    totalRuns: 41,
    lastUsed: "Yesterday",
  },
  {
    slug: "tone-adjuster-casual",
    name: "Tone Adjuster (Casual)",
    description: "Makes stiff, corporate copy feel warm, approachable, and conversational — without losing clarity.",
    category: "optimization",
    model: "Claude 3.5 Sonnet",
    tools: ["RecallBrandVoice", "CheckVoiceConsistency", "ScoreReadability"],
    qualityThreshold: 0.75,
    avgScore: 0.88,
    totalRuns: 38,
    lastUsed: "2 days ago",
  },
  {
    slug: "accessibility-checker",
    name: "Accessibility Checker",
    description: "Reviews content for accessibility issues — reading level, plain language, screen reader compatibility, and cognitive load.",
    category: "evaluation",
    model: "Claude 3.5 Sonnet",
    tools: ["CheckAccessibility", "ScoreReadability", "RunLinter"],
    qualityThreshold: 0.85,
    avgScore: 0.92,
    totalRuns: 33,
    lastUsed: "4 hours ago",
  },
  {
    slug: "onboarding-flow-writer",
    name: "Onboarding Flow Writer",
    description: "Writes complete onboarding sequences — welcome screens, tooltips, progress indicators, and success celebrations.",
    category: "writing",
    model: "Claude 3.5 Sonnet",
    tools: ["RunLinter", "ScoreReadability", "CheckAccessibility", "RecallBrandVoice", "RecallContext"],
    qualityThreshold: 0.80,
    avgScore: 0.86,
    totalRuns: 21,
    lastUsed: "3 days ago",
  },
  {
    slug: "changelog-writer",
    name: "Changelog Writer",
    description: "Turns feature specs and commit logs into user-friendly release notes and changelog entries.",
    category: "writing",
    model: "GPT-4o",
    tools: ["RecallBrandVoice", "ScoreReadability"],
    qualityThreshold: 0.70,
    avgScore: 0.84,
    totalRuns: 17,
    lastUsed: "1 week ago",
  },
  {
    slug: "content-localizer",
    name: "Content Localizer",
    description: "Adapts content for different markets and locales — not just translation, but cultural adaptation of tone, metaphors, and examples.",
    category: "translation",
    model: "GPT-4o",
    tools: ["RecallBrandVoice", "ScoreReadability", "RecallContext"],
    qualityThreshold: 0.75,
    avgScore: 0.81,
    totalRuns: 12,
    lastUsed: "5 days ago",
  },
  {
    slug: "notification-writer",
    name: "Notification Writer",
    description: "Writes push notifications, email subject lines, and in-app alerts that drive action without annoying users.",
    category: "writing",
    model: "Claude 3.5 Sonnet",
    tools: ["RunLinter", "ScoreReadability", "RecallBrandVoice"],
    qualityThreshold: 0.75,
    avgScore: 0.89,
    totalRuns: 29,
    lastUsed: "6 hours ago",
  },
  {
    slug: "help-doc-writer",
    name: "Help Doc Writer",
    description: "Writes clear help center articles, FAQ entries, and troubleshooting guides from product specs or support tickets.",
    category: "writing",
    model: "Claude 3.5 Sonnet",
    tools: ["RunLinter", "ScoreReadability", "CheckAccessibility", "RecallBrandVoice", "RecallContext"],
    qualityThreshold: 0.80,
    avgScore: 0.87,
    totalRuns: 15,
    lastUsed: "2 days ago",
  },
];

export const categoryLabels: Record<AgentCategory, string> = {
  writing: "Writing",
  evaluation: "Evaluation",
  optimization: "Optimization",
  translation: "Localization",
};

export const categoryColors: Record<AgentCategory, string> = {
  writing: "bg-blue-50 text-blue-700 border-blue-100",
  evaluation: "bg-purple-50 text-purple-700 border-purple-100",
  optimization: "bg-amber-50 text-amber-700 border-amber-100",
  translation: "bg-emerald-50 text-emerald-700 border-emerald-100",
};
