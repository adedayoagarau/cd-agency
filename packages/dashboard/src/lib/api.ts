import { getStoredKeys } from "./api-keys-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class CDAgencyAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE;
  }

  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const keys = getStoredKeys();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (keys.anthropic) headers["X-Anthropic-Key"] = keys.anthropic;
    if (keys.openai) headers["X-OpenAI-Key"] = keys.openai;
    // Merge with any custom headers
    if (options?.headers) {
      Object.assign(headers, options.headers);
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }
    return res.json();
  }

  // Agents
  async listAgents() {
    return this.fetch<{ agents: APIAgent[] }>("/api/v2/agents");
  }

  async getAgent(slug: string) {
    return this.fetch<APIAgentDetail>(`/api/v2/agents/${slug}`);
  }

  async runAgent(params: {
    agent_slug: string;
    content: string;
    model?: string;
    enable_council?: boolean;
  }) {
    return this.fetch<RunResult>("/api/v2/agents/run", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Streaming (WebSocket)
  streamAgentRun(params: { agent_slug: string; content: string }): WebSocket {
    const wsUrl = this.baseUrl.replace("http", "ws");
    const ws = new WebSocket(`${wsUrl}/api/v2/agents/run/stream`);
    const keys = getStoredKeys();
    ws.onopen = () => ws.send(JSON.stringify({
      ...params,
      anthropic_key: keys.anthropic,
      openai_key: keys.openai,
    }));
    return ws;
  }

  // Brand DNA
  async getBrandDNA() {
    return this.fetch<BrandDNAData>("/api/v2/brand-dna");
  }

  async updateBrandDNA(update: Partial<BrandDNAData>) {
    return this.fetch("/api/v2/brand-dna", {
      method: "PUT",
      body: JSON.stringify(update),
    });
  }

  async ingestBrandContent(content: string) {
    return this.fetch<{ patterns_extracted: number }>("/api/v2/brand-dna/ingest", {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  }

  // Memory
  async searchMemory(query: string, scope?: string, limit?: number) {
    return this.fetch<{ results: MemoryEntryData[] }>("/api/v2/memory/search", {
      method: "POST",
      body: JSON.stringify({ query, scope, limit }),
    });
  }

  async getMemoryStats() {
    return this.fetch<MemoryStatsData>("/api/v2/memory/stats");
  }

  // Connectors
  async listConnectors() {
    return this.fetch<{ connectors: ConnectorData[] }>("/api/v2/connectors");
  }

  async syncConnector(name: string, mode = "pull", dryRun = false) {
    return this.fetch(`/api/v2/connectors/${name}/sync`, {
      method: "POST",
      body: JSON.stringify({ connector_name: name, sync_mode: mode, dry_run: dryRun }),
    });
  }

  async connectorHealth(name: string) {
    return this.fetch<{ status: string }>(`/api/v2/connectors/${name}/health`);
  }

  // History
  async getHistory(params?: {
    agent?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = new URLSearchParams();
    if (params?.agent) query.set("agent", params.agent);
    if (params?.status) query.set("status", params.status);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    const qs = query.toString();
    return this.fetch<{ runs: HistoryRunData[]; total: number }>(
      `/api/v2/history${qs ? `?${qs}` : ""}`
    );
  }

  // Config
  async getQualityThresholds() {
    return this.fetch<Record<string, number>>("/api/v2/config/quality-thresholds");
  }

  async updateQualityThresholds(thresholds: Record<string, number>) {
    return this.fetch("/api/v2/config/quality-thresholds", {
      method: "PUT",
      body: JSON.stringify(thresholds),
    });
  }

  async getCouncilStatus() {
    return this.fetch<CouncilStatusData>("/api/v2/council/status");
  }

  // Scoring
  async scoreReadability(text: string) {
    return this.fetch<ReadabilityResult>("/api/v2/score/readability", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  async scoreLint(text: string) {
    return this.fetch<LintResult>("/api/v2/score/lint", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  async scoreA11y(text: string) {
    return this.fetch<A11yResult>("/api/v2/score/a11y", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  async scoreAll(text: string) {
    return this.fetch<CombinedScoreResult>("/api/v2/score/all", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  // Validation
  async validate(text: string, elementType: string, platform?: string) {
    return this.fetch<ValidateResult>("/api/v2/validate", {
      method: "POST",
      body: JSON.stringify({ text, element_type: elementType, platform }),
    });
  }

  async getElementTypes() {
    return this.fetch<ElementTypeInfo[]>("/api/v2/validate/element-types");
  }

  // Workflows
  async listWorkflows() {
    return this.fetch<WorkflowSummary[]>("/api/v2/workflows");
  }

  async getWorkflow(slug: string) {
    return this.fetch<WorkflowDetail>(`/api/v2/workflows/${slug}`);
  }

  async runWorkflow(slug: string, input: Record<string, string>) {
    return this.fetch<WorkflowRunResult>(`/api/v2/workflows/${slug}/run`, {
      method: "POST",
      body: JSON.stringify({ input }),
    });
  }

  // Presets
  async listPresets() {
    return this.fetch<PresetSummary[]>("/api/v2/presets");
  }

  async getPreset(name: string) {
    return this.fetch<PresetDetail>(`/api/v2/presets/${name}`);
  }

  // Council config
  async updateCouncilConfig(config: Partial<CouncilStatusData>) {
    return this.fetch("/api/v2/council/config", {
      method: "PUT",
      body: JSON.stringify(config),
    });
  }

  // Connector disconnect
  async disconnectConnector(name: string) {
    return this.fetch(`/api/v2/connectors/${name}`, { method: "DELETE" });
  }

  // Health
  async healthCheck() {
    return this.fetch<{ status: string; version: string }>("/api/v2/health");
  }

  // Export
  async exportContent(entries: ExportEntry[], format: string) {
    const res = await fetch(`${this.baseUrl}/api/v2/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries, format }),
    });
    if (!res.ok) throw new Error(`Export failed: ${res.status}`);
    return res.text();
  }

  async getExportFormats() {
    return this.fetch<{ id: string; label: string; extension: string }[]>("/api/v2/export/formats");
  }

  // Scrape
  async scrapeUrl(url: string) {
    return this.fetch<ScrapeResult>("/api/v2/scrape", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  }

  // History search
  async searchHistory(query: string) {
    return this.fetch<HistorySearchResult[]>(`/api/v2/history/search?q=${encodeURIComponent(query)}`);
  }

  // History version diff
  async getHistoryVersion(versionId: string) {
    return this.fetch<HistorySearchResult>(`/api/v2/history/${encodeURIComponent(versionId)}`);
  }
}

export const api = new CDAgencyAPI();

// ── API Types ──

export interface APIAgent {
  slug: string;
  name: string;
  description: string;
  model: string;
  tools: string[];
  tags: string[];
  evaluation: Record<string, number>;
  threshold: number;
}

export interface APIAgentDetail extends APIAgent {
  inputs: { name: string; type: string; required: boolean; description: string }[];
  outputs: { name: string; type: string; description: string }[];
}

export interface RunResult {
  run_id: string;
  agent: string;
  output: string;
  evaluation: Record<string, number>;
  composite_score: number;
  passed: boolean;
  iterations: number;
  council_result?: Record<string, unknown>;
  duration_ms: number;
}

export interface BrandDNAData {
  voice_patterns: {
    dimension: string;
    value: string;
    confidence: number;
    source: string;
  }[];
  terminology: {
    term: string;
    preferred: string;
    avoid: string;
    severity: "required" | "preferred";
  }[];
  style_rules: {
    rule: string;
    severity: "required" | "preferred";
    category: string;
  }[];
  sources: string[];
}

export interface MemoryEntryData {
  key: string;
  value: string;
  category: string;
  source_agent: string;
  scope: "session" | "project" | "workspace";
  timestamp: string;
  relevance_score?: number;
}

export interface MemoryStatsData {
  session_count: number;
  project_count: number;
  workspace_count: number;
  total_entries: number;
}

export interface ConnectorData {
  name: string;
  type: string;
  status: string;
  last_sync?: string;
  entry_count: number;
}

export interface HistoryRunData {
  agent_slug: string;
  composite_score: number;
  passed: boolean;
  iteration_count: number;
  timestamp: string;
  scores: Record<string, number>;
}

export interface CouncilStatusData {
  enabled: boolean;
  min_models: number;
  consensus_method: string;
  trigger_conditions: string[];
}

// Scoring types
export interface ReadabilityResult {
  word_count: number;
  sentence_count: number;
  flesch_reading_ease: number;
  flesch_kincaid_grade: number;
  avg_sentence_length: number;
  reading_time_seconds: number;
  grade_label: string;
  ease_label: string;
}

export interface LintIssue {
  rule: string;
  passed: boolean;
  severity: string;
  message: string;
  suggestion: string;
}

export interface LintResult {
  issues: LintIssue[];
  passed_count: number;
  failed_count: number;
  total_rules: number;
}

export interface A11yIssue {
  rule: string;
  severity: string;
  message: string;
  wcag_criterion: string;
  suggestion: string;
}

export interface A11yResult {
  passed: boolean;
  issue_count: number;
  reading_grade: number;
  target_grade: number;
  issues: A11yIssue[];
}

export interface CombinedScoreResult {
  readability: ReadabilityResult;
  lint: LintResult;
  a11y: A11yResult;
}

// Validation types
export interface ValidateViolation {
  rule: string;
  severity: string;
  message: string;
  value?: string;
  limit?: number;
}

export interface ValidateResult {
  passed: boolean;
  error_count: number;
  warning_count: number;
  violations: ValidateViolation[];
  summary: string;
}

export interface ElementTypeInfo {
  type: string;
  max_chars: number;
  label: string;
}

// Workflow types
export interface WorkflowSummary {
  slug: string;
  name: string;
  description: string;
  step_count: number;
}

export interface WorkflowStep {
  name: string;
  agent: string;
  parallel_group?: string;
  condition?: string;
}

export interface WorkflowDetail extends WorkflowSummary {
  steps: WorkflowStep[];
}

export interface WorkflowStepResult {
  step_name: string;
  agent_name: string;
  output: string;
  skipped: boolean;
  error?: string;
}

export interface WorkflowRunResult {
  workflow_name: string;
  steps: WorkflowStepResult[];
  final_output: string;
  total_tokens: number;
  latency_ms: number;
}

// Preset types
export interface PresetSummary {
  name: string;
  filename: string;
}

export interface PresetDetail extends PresetSummary {
  tone_descriptors: string[];
  do_rules: string[];
  dont_rules: string[];
  sample_content: string[];
  character_limits: Record<string, number>;
  terminology: Record<string, string>;
}

// Export entry for the export API
export interface ExportEntry {
  id?: string;
  source: string;
  target: string;
  context?: string;
  agent?: string;
  notes?: string;
}

// Scrape result
export interface ScrapeResult {
  url: string;
  title: string;
  description: string;
  headings: string[];
  paragraphs: string[];
  links: string[];
  images: string[];
  meta: Record<string, string>;
  raw_text: string;
}

// History search result
export interface HistorySearchResult {
  id: string;
  timestamp: number;
  agent_name: string;
  agent_slug: string;
  input_text: string;
  output_text: string;
  input_fields: Record<string, string>;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}
