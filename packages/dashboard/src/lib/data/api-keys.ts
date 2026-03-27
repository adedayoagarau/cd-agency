export interface LLMProvider {
  id: string;
  name: string;
  connected: boolean;
  maskedKey: string | null;
  lastUsed: string | null;
}

export interface CMSCredential {
  id: string;
  platform: string;
  type: string;
  maskedKey: string;
  lastUsed: string;
}

export interface WorkspaceKey {
  id: string;
  name: string;
  maskedKey: string;
  created: string;
  lastUsed: string;
}

export const llmProviders: LLMProvider[] = [
  { id: "anthropic", name: "Anthropic", connected: true, maskedKey: "sk-ant-...7a4b", lastUsed: "2 min ago" },
  { id: "openai", name: "OpenAI", connected: true, maskedKey: "sk-...9x2f", lastUsed: "3 hours ago" },
  { id: "openrouter", name: "OpenRouter", connected: false, maskedKey: null, lastUsed: null },
];

export const cmsCredentials: CMSCredential[] = [
  { id: "contentful", platform: "Contentful", type: "Space ID + Access Token", maskedKey: "cfpat-...3k9m", lastUsed: "2 min ago" },
  { id: "figma", platform: "Figma", type: "Personal Access Token", maskedKey: "figd_...x7p2", lastUsed: "15 min ago" },
  { id: "notion", platform: "Notion", type: "Integration Key", maskedKey: "secret_...n4w8", lastUsed: "1 hour ago" },
];

export const workspaceKeys: WorkspaceKey[] = [
  { id: "k1", name: "Production API", maskedKey: "cda_8f...b2x4", created: "Feb 10, 2026", lastUsed: "1 hour ago" },
  { id: "k2", name: "CI/CD Pipeline", maskedKey: "cda_3a...m7k9", created: "Mar 1, 2026", lastUsed: "Yesterday" },
];
