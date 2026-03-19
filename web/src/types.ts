export interface AgentSummary {
  slug: string;
  name: string;
  description: string;
  tags: string[];
}

export interface AgentDetail extends AgentSummary {
  inputs: { name: string; type: string; required: boolean; description: string }[];
  outputs: { name: string; type: string; description: string }[];
  related_agents: string[];
  version: string;
  difficulty_level: string;
}

export interface AgentRunResponse {
  content: string;
  agent_name: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ReadabilityScore {
  word_count: number;
  character_count: number;
  sentence_count: number;
  flesch_reading_ease: number;
  flesch_kincaid_grade: number;
  grade_label: string;
  ease_label: string;
  reading_time_seconds: number;
}

export interface LintIssue {
  rule: string;
  passed: boolean;
  severity: string;
  message: string;
  suggestion: string;
}

export interface LintResponse {
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

export interface A11yResponse {
  passed: boolean;
  label: string;
  issue_count: number;
  issues: A11yIssue[];
}

export interface CombinedScore {
  readability: ReadabilityScore;
  lint: LintResponse;
  a11y: A11yResponse;
}

export interface WorkflowSummary {
  slug: string;
  name: string;
  description: string;
  step_count: number;
}

export interface WorkflowDetail extends WorkflowSummary {
  steps: { name: string; agent: string; parallel_group?: string; condition?: string }[];
}

export interface StepResult {
  step_name: string;
  agent_name: string;
  output: string;
  skipped: boolean;
  error?: string;
}

export interface WorkflowRunResponse {
  workflow_name: string;
  steps: StepResult[];
  final_output: string;
  total_tokens: number;
  latency_ms: number;
}

export interface ScrapeResponse {
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

export interface VersionEntry {
  id: string;
  timestamp: number;
  agent_name: string;
  agent_slug: string;
  input_text: string;
  output_text: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}

export interface PresetSummary {
  name: string;
  filename: string;
}

export type Tab = "chat" | "form" | "workflow" | "batch" | "history" | "scrape";

export interface ProviderConfig {
  name: string;
  label: string;
  defaultModel: string;
  models: string[];
  key_placeholder: string;
}
