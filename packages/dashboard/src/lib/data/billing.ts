export interface Plan {
  id: string;
  name: string;
  price: string;
  period: string;
  features: string[];
  limits: { runs: string; projects: string; users: string; extras: string };
  isCurrent?: boolean;
  isPopular?: boolean;
}

export const plans: Plan[] = [
  { id: "free", name: "Free", price: "$0", period: "/month", features: ["50 agent runs", "1 project", "1 user", "Community support"], limits: { runs: "50", projects: "1", users: "1", extras: "\u2014" } },
  { id: "pro", name: "Pro", price: "$29", period: "/month", features: ["500 agent runs", "5 projects", "1 user", "Brand DNA", "Connectors", "Email support"], limits: { runs: "500", projects: "5", users: "1", extras: "Brand DNA" }, isCurrent: true, isPopular: true },
  { id: "team", name: "Team", price: "$79", period: "/seat/mo", features: ["Unlimited runs", "Unlimited projects", "Team features", "All connectors", "Priority support"], limits: { runs: "Unlimited", projects: "Unlimited", users: "Team", extras: "All features" } },
  { id: "enterprise", name: "Enterprise", price: "Custom", period: "", features: ["Unlimited everything", "SSO/SAML", "SLA", "Dedicated support", "Custom integrations"], limits: { runs: "Unlimited", projects: "Unlimited", users: "SSO+", extras: "All + SLA" } },
];

export const usageMeters = [
  { label: "Agent Runs", current: 347, max: 500, unit: "runs" },
  { label: "Tokens Consumed", current: 1.2, max: 2, unit: "M tokens" },
  { label: "Connector Syncs", current: 89, max: 200, unit: "syncs" },
  { label: "Memory Storage", current: 2.4, max: 50, unit: "MB" },
];

export const invoices = [
  { id: "inv-001", date: "Mar 1, 2026", amount: "$29.00", status: "paid" as const },
  { id: "inv-002", date: "Feb 1, 2026", amount: "$29.00", status: "paid" as const },
  { id: "inv-003", date: "Jan 1, 2026", amount: "$29.00", status: "paid" as const },
];

export const apiKeyProviders = [
  { name: "Anthropic", connected: true, savings: "$8/mo" },
  { name: "OpenAI", connected: true, savings: "$4/mo" },
  { name: "OpenRouter", connected: false, savings: null },
];
