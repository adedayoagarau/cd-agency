import type {
  AgentDetail,
  AgentRunResponse,
  AgentSummary,
  CombinedScore,
  ConversationMessage,
  PresetSummary,
  ProviderConfig,
  ScrapeResponse,
  VersionEntry,
  WorkflowDetail,
  WorkflowRunResponse,
  WorkflowSummary,
} from "./types";

const BASE = "/api/v1";

function getProviderConfig(): { provider: string; apiKey: string; model: string } {
  const provider = localStorage.getItem("cd-agency-provider") || "anthropic";
  let apiKey = "";
  try {
    const keys = JSON.parse(localStorage.getItem("cd-agency-provider-keys") || "{}");
    apiKey = keys[provider] || "";
  } catch {
    // Fallback to legacy key
    apiKey = localStorage.getItem("cd-agency-api-key") || "";
  }
  const model = localStorage.getItem("cd-agency-model") || "";
  return { provider, apiKey, model };
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const { provider, apiKey, model } = getProviderConfig();
  if (apiKey) {
    headers["X-LLM-Key"] = apiKey;
    // Backward compat: also send X-Anthropic-Key when using Anthropic
    if (provider === "anthropic") {
      headers["X-Anthropic-Key"] = apiKey;
    }
  }
  if (provider) headers["X-Provider"] = provider;
  if (model) headers["X-Model"] = model;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function requestText(
  path: string,
  options: RequestInit = {}
): Promise<string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.text();
}

// Agents
export const listAgents = () => request<AgentSummary[]>("/agents");
export const getAgent = (slug: string) =>
  request<AgentDetail>(`/agents/${slug}`);
export const searchAgents = (q: string) =>
  request<AgentSummary[]>(`/agents/search?q=${encodeURIComponent(q)}`);

export const runAgent = (slug: string, input: Record<string, string>) =>
  request<AgentRunResponse>(`/agents/${slug}/run`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });

export const chatWithAgent = (slug: string, messages: ConversationMessage[]) =>
  request<AgentRunResponse>(`/agents/${slug}/chat`, {
    method: "POST",
    body: JSON.stringify({ messages }),
  });

export const batchRunAgent = (
  slug: string,
  items: { input: Record<string, string> }[]
) =>
  request<AgentRunResponse[]>(`/agents/${slug}/batch`, {
    method: "POST",
    body: JSON.stringify({ items }),
  });

// Scoring
export const scoreAll = (text: string) =>
  request<CombinedScore>("/score/all", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

// Presets
export const listPresets = () => request<PresetSummary[]>("/presets");

// Workflows
export const listWorkflows = () => request<WorkflowSummary[]>("/workflows");
export const getWorkflow = (slug: string) =>
  request<WorkflowDetail>(`/workflows/${slug}`);
export const runWorkflow = (slug: string, input: Record<string, string>) =>
  request<WorkflowRunResponse>(`/workflows/${slug}/run`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });

// Scrape
export const scrapeUrl = (url: string) =>
  request<ScrapeResponse>("/scrape", {
    method: "POST",
    body: JSON.stringify({ url }),
  });

// Providers
export const listProviders = () => request<ProviderConfig[]>("/providers");

// History
export const listHistory = (count = 20) =>
  request<VersionEntry[]>(`/history?count=${count}`);

// Export
export const exportContent = (
  entries: { source: string; target: string; context?: string }[],
  format: string
) =>
  requestText("/export", {
    method: "POST",
    body: JSON.stringify({ entries, format }),
  });
