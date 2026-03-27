export type MemoryScope = "session" | "project" | "workspace";

export interface MemoryEntry {
  id: string;
  scope: MemoryScope;
  content: string;
  source: string;
  tags: string[];
  createdAt: string;
  relevance?: number;
}

export const memoryEntries: MemoryEntry[] = [
  { id: "m1", scope: "workspace", content: "Brand voice should be professional but approachable. Avoid corporate jargon. Use contractions to feel human.", source: "Brand Voice Evaluator", tags: ["voice", "brand"], createdAt: "2 hours ago" },
  { id: "m2", scope: "project", content: "The checkout flow redesign uses a 3-step wizard pattern. Error messages should reference step numbers.", source: "Error Message Crafter", tags: ["checkout", "errors"], createdAt: "4 hours ago" },
  { id: "m3", scope: "session", content: "User prefers shorter button labels (2-3 words max). Current task: upload flow microcopy.", source: "Microcopy Writer", tags: ["buttons", "upload"], createdAt: "15 min ago" },
  { id: "m4", scope: "workspace", content: "Terminology: Always use 'workspace' not 'project'. 'Sign up' not 'register'. 'Team member' not 'user'.", source: "Brand Voice Evaluator", tags: ["terminology", "brand"], createdAt: "1 day ago" },
  { id: "m5", scope: "project", content: "Onboarding flow targets: <8th grade reading level, max 15 words per tooltip, progressive disclosure pattern.", source: "Onboarding Flow Writer", tags: ["onboarding", "readability"], createdAt: "2 days ago" },
  { id: "m6", scope: "session", content: "Testing formal tone adjustments for the enterprise landing page. Client wants 'sophisticated but not stuffy'.", source: "Tone Adjuster (Formal)", tags: ["tone", "enterprise"], createdAt: "30 min ago" },
  { id: "m7", scope: "workspace", content: "Accessibility standard: All UI text must pass WCAG 2.1 AA. Reading level target: Grade 6-8.", source: "Accessibility Checker", tags: ["a11y", "standards"], createdAt: "3 days ago" },
  { id: "m8", scope: "project", content: "SEO meta descriptions should be 150-160 characters. Include primary keyword in first 60 characters.", source: "SEO Meta Generator", tags: ["seo", "meta"], createdAt: "5 hours ago" },
];

export const scopeColors: Record<MemoryScope, string> = {
  session: "bg-blue-50 text-blue-700 border-blue-100",
  project: "bg-brand-50 text-brand-700 border-brand-100",
  workspace: "bg-emerald-50 text-emerald-700 border-emerald-100",
};
