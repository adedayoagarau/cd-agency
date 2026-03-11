import * as vscode from "vscode";

/** Describes a single CD Agency agent. */
export interface Agent {
  slug: string;
  name: string;
  description: string;
  tags: string[];
}

/** Result returned after running an agent on text. */
export interface AgentResult {
  /** Agent display name. */
  agent: string;
  /** The original text that was sent to the agent. */
  original: string;
  /** The agent's full response content. */
  content: string;
  /** Model used for generation. */
  model: string;
}

/** Readability metrics from the scoring API. */
export interface ReadabilityResult {
  word_count: number;
  flesch_reading_ease: number;
  flesch_kincaid_grade: number;
  grade_label: string;
  ease_label: string;
}

/** A single lint rule result from the API. */
export interface LintIssue {
  rule: string;
  passed: boolean;
  severity: string;
  message: string;
  suggestion: string;
  matches: string[];
}

/** Lint result from the API. */
export interface LintResult {
  issues: LintIssue[];
  passed_count: number;
  failed_count: number;
  total_rules: number;
}

/** Accessibility check result. */
export interface A11yResult {
  passed: boolean;
  label: string;
  issue_count: number;
  issues: Array<{
    rule: string;
    severity: string;
    message: string;
    suggestion: string;
  }>;
}

/** Combined scoring result from /api/v1/score/all. */
export interface ScoreResult {
  readability: ReadabilityResult;
  lint: LintResult;
  a11y: A11yResult;
}

/** Design system preset definition. */
export interface Preset {
  name: string;
  filename: string;
}

function getApiUrl(): string {
  const config = vscode.workspace.getConfiguration("cdAgency");
  return config.get<string>("apiUrl", "http://localhost:8000");
}

function getDefaultPreset(): string {
  const config = vscode.workspace.getConfiguration("cdAgency");
  return config.get<string>("defaultPreset", "material-design");
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = getApiUrl();
  const url = `${baseUrl}${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Unknown network error";
    throw new Error(
      `Failed to connect to CD Agency API at ${baseUrl}. ` +
        `Ensure the server is running. (${message})`
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? "";
    } catch {
      // body wasn't JSON — ignore
    }
    throw new Error(
      `CD Agency API error ${response.status}: ${detail || response.statusText}`
    );
  }

  return (await response.json()) as T;
}

/** Fetch the list of available agents. */
export async function listAgents(): Promise<Agent[]> {
  return request<Agent[]>("/api/v1/agents");
}

/** Run an agent on the given text. Returns a normalized result. */
export async function runAgent(
  slug: string,
  text: string
): Promise<AgentResult> {
  const preset = getDefaultPreset();
  const data = await request<{
    content: string;
    agent_name: string;
    model: string;
  }>(`/api/v1/agents/${encodeURIComponent(slug)}/run`, {
    method: "POST",
    body: JSON.stringify({ input: { text }, preset }),
  });
  return {
    agent: data.agent_name,
    original: text,
    content: data.content,
    model: data.model,
  };
}

/** Score a piece of text (readability, a11y, lint). */
export async function scoreText(text: string): Promise<ScoreResult> {
  return request<ScoreResult>("/api/v1/score/all", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

/** Lint a piece of text and return the lint result. */
export async function lintText(text: string): Promise<LintResult> {
  return request<LintResult>("/api/v1/score/lint", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

/** Fetch available design system presets. */
export async function getPresets(): Promise<Preset[]> {
  return request<Preset[]>("/api/v1/presets");
}
