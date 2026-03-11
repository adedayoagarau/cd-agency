// CD Agency Figma Plugin — UI Thread
// Runs inside the plugin iframe. Handles rendering, API communication,
// and message passing to/from the Figma sandbox (code.ts).

// =====================================================================
// Types
// =====================================================================

interface AgentDef {
  id: string;
  label: string;
  keywords: string[];
}

interface Suggestion {
  text: string;
  rationale: string;
  recommended?: boolean;
}

interface ScoreResult {
  readability?: { grade: number; ease: number };
  a11y?: { passed: boolean; issues: number };
}

interface RunResult {
  content: string;
  suggestions: Suggestion[];
  score?: ScoreResult;
  model?: string;
  tokens?: { input: number; output: number };
}

interface HistoryEntry {
  id: string;
  agent: string;
  agentLabel: string;
  originalText: string;
  result: RunResult;
  preset: string;
  timestamp: number;
}

interface SelectionMsg {
  type: "selection";
  text: string;
  nodeId: string;
  nodeName: string;
  layerContext: string;
}

interface NoSelectionMsg {
  type: "no-selection";
  reason: string;
}

type PluginMsg =
  | SelectionMsg
  | NoSelectionMsg
  | { type: "apply-success"; text: string }
  | { type: "apply-error"; error: string };

// =====================================================================
// Agent catalogue
// =====================================================================

const AGENTS: AgentDef[] = [
  { id: "microcopy-review-agent",            label: "Microcopy Review",              keywords: ["review","microcopy","copy","label","button","text"] },
  { id: "error-message-architect",           label: "Error Message Architect",       keywords: ["error","fail","invalid","wrong","oops","sorry","problem"] },
  { id: "cta-optimization-specialist",       label: "CTA Optimization Specialist",   keywords: ["cta","button","submit","sign up","start","try","get","buy","subscribe"] },
  { id: "accessibility-content-auditor",     label: "Accessibility Auditor",         keywords: ["accessibility","a11y","screen reader","alt"] },
  { id: "tone-evaluation-agent",             label: "Tone Evaluator",                keywords: ["tone","voice","brand","feel","mood"] },
  { id: "empty-state-placeholder-specialist",label: "Empty State Specialist",        keywords: ["empty","no results","nothing","placeholder","zero","blank"] },
  { id: "onboarding-flow-designer",          label: "Onboarding Flow Designer",      keywords: ["onboard","welcome","getting started","intro","setup","first"] },
  { id: "notification-content-designer",     label: "Notification Designer",         keywords: ["notification","alert","toast","banner","message","reminder"] },
  { id: "mobile-ux-writer",                  label: "Mobile UX Writer",              keywords: ["mobile","phone","app","touch","swipe"] },
  { id: "conversational-ai-designer",        label: "Conversational AI Designer",    keywords: ["chat","conversation","bot","assistant","dialog"] },
  { id: "search-experience-writer",          label: "Search Experience Writer",      keywords: ["search","find","filter","query","results"] },
  { id: "privacy-legal-content-simplifier",  label: "Privacy / Legal Simplifier",    keywords: ["privacy","legal","terms","consent","cookie","gdpr","policy"] },
  { id: "localization-content-strategist",   label: "Localization Strategist",       keywords: ["localization","translate","i18n","international","language"] },
  { id: "technical-documentation-writer",    label: "Technical Doc Writer",          keywords: ["docs","documentation","technical","api","guide","reference"] },
  { id: "content-designer-generalist",       label: "Content Designer (Generalist)", keywords: ["general","content","design","write","ux"] },
];

// =====================================================================
// Constants & state
// =====================================================================

const DEFAULT_URL  = "http://localhost:8000";
const HIST_KEY     = "cd-agency-history";
const MAX_HIST     = 50;

let apiUrl  = DEFAULT_URL;
let apiKey  = "";
let selection: SelectionMsg | null = null;
let nodeId  = "";
let history: HistoryEntry[] = [];

// =====================================================================
// Helpers
// =====================================================================

const $ = (s: string) => document.querySelector(s) as HTMLElement | null;
const $$ = (s: string) => document.querySelectorAll(s);

function showScreen(id: string): void {
  $$(".screen").forEach(el => el.classList.remove("active"));
  const el = $(`#screen-${id}`);
  if (el) el.classList.add("active");
}

function toast(msg: string, ms = 2000): void {
  const el = $("#toast")!;
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), ms);
}

function post(msg: Record<string, unknown>): void {
  parent.postMessage({ pluginMessage: msg }, "*");
}

function esc(s: string): string {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function escAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function timeAgo(ts: number): string {
  const m = Math.floor((Date.now() - ts) / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function agentLabel(id: string): string {
  return AGENTS.find(a => a.id === id)?.label || id;
}

// =====================================================================
// Storage
// =====================================================================

function loadSettings(): void {
  try {
    apiUrl = localStorage.getItem("cd-agency-url") || DEFAULT_URL;
    apiKey = localStorage.getItem("cd-agency-key") || "";
  } catch {
    apiUrl = DEFAULT_URL;
    apiKey = "";
  }
}

function saveSettings(url: string, key: string): void {
  apiUrl = url;
  apiKey = key;
  try {
    localStorage.setItem("cd-agency-url", url);
    localStorage.setItem("cd-agency-key", key);
  } catch { /* noop */ }
}

function loadHistory(): void {
  try {
    history = JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
  } catch { history = []; }
}

function saveHistory(): void {
  try {
    localStorage.setItem(HIST_KEY, JSON.stringify(history.slice(0, MAX_HIST)));
  } catch { /* noop */ }
}

function pushHistory(e: HistoryEntry): void {
  history.unshift(e);
  if (history.length > MAX_HIST) history.pop();
  saveHistory();
}

// =====================================================================
// Auto-suggest agents based on text content
// =====================================================================

function suggest(text: string): AgentDef[] {
  const lc = text.toLowerCase();
  const scored = AGENTS.map(a => ({
    a,
    s: a.keywords.reduce((n, kw) => n + (lc.includes(kw) ? 1 : 0), 0),
  })).filter(x => x.s > 0);
  scored.sort((a, b) => b.s - a.s);
  return scored.slice(0, 3).map(x => x.a);
}

// =====================================================================
// API
// =====================================================================

async function apiCall(path: string, body?: Record<string, unknown>): Promise<unknown> {
  const url = `${apiUrl.replace(/\/+$/, "")}${path}`;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) headers["X-API-Key"] = apiKey;

  const resp = await fetch(url, {
    method: body ? "POST" : "GET",
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!resp.ok) {
    const t = await resp.text().catch(() => "Unknown error");
    throw new Error(`API ${resp.status}: ${t}`);
  }
  return resp.json();
}

async function callRunAgent(
  agentId: string,
  text: string,
  preset: string,
  extra: Record<string, string>,
): Promise<RunResult> {
  const input: Record<string, string> = { text, ...extra };
  const body: Record<string, unknown> = { input };
  if (preset) body.preset = preset;

  const data = (await apiCall(`/api/v1/agents/${agentId}/run`, body)) as Record<string, unknown>;
  const content = (data.content as string) || "";
  return {
    content,
    suggestions: parseSuggestions(content),
    score: undefined,
    model: (data.model as string) || undefined,
    tokens: data.input_tokens
      ? { input: data.input_tokens as number, output: data.output_tokens as number }
      : undefined,
  };
}

async function callScore(text: string): Promise<ScoreResult> {
  const data = (await apiCall("/api/v1/score/all", { text })) as Record<string, unknown>;
  const readability = data.readability as Record<string, unknown> | undefined;
  const a11y = data.a11y as Record<string, unknown> | undefined;
  return {
    readability: readability
      ? { grade: readability.flesch_kincaid_grade as number, ease: readability.flesch_reading_ease as number }
      : undefined,
    a11y: a11y
      ? { passed: a11y.passed as boolean, issues: a11y.issue_count as number }
      : undefined,
  };
}

// =====================================================================
// Parse suggestions from free-text agent response
// =====================================================================

function parseSuggestions(content: string): Suggestion[] {
  const out: Suggestion[] = [];

  // Pattern 1: "quoted text" - rationale  (or curly quotes)
  const p1 = /["\u201C]([^"\u201D]+)["\u201D]\s*[-\u2014:]+\s*(.+)/g;
  let m: RegExpExecArray | null;
  while ((m = p1.exec(content)) !== null) {
    out.push({ text: m[1].trim(), rationale: m[2].trim(), recommended: out.length === 0 });
  }
  if (out.length) return out;

  // Pattern 2: numbered list  1. "text" - rationale
  const p2 = /\d+[\.\)]\s*["\u201C]?([^"\u201D\n]+)["\u201D]?\s*[-\u2014:]+\s*(.+)/g;
  while ((m = p2.exec(content)) !== null) {
    out.push({ text: m[1].trim(), rationale: m[2].trim(), recommended: out.length === 0 });
  }
  if (out.length) return out;

  // Fallback: first meaningful line is the suggestion
  const lines = content.trim().split("\n").filter(l => l.trim());
  if (lines.length) {
    out.push({
      text: lines[0].replace(/^[\*\-\#\d\.\)]+\s*/, "").replace(/["\u201C\u201D]/g, "").trim(),
      rationale: lines.length > 1
        ? lines.slice(1).join(" ").trim().substring(0, 200)
        : "Agent suggestion",
      recommended: true,
    });
  }
  return out;
}

// =====================================================================
// Render helpers
// =====================================================================

function renderQuickActions(text: string): void {
  const wrap = $("#qa-list")!;
  const sec  = $("#qa-section")!;
  wrap.innerHTML = "";

  const suggestions = suggest(text);
  const items = suggestions.length
    ? suggestions.map((a, i) => ({ label: a.label, id: a.id, first: i === 0 }))
    : [
        { label: "Review Microcopy",    id: "microcopy-review-agent",        first: false },
        { label: "Check Accessibility", id: "accessibility-content-auditor", first: false },
        { label: "Optimize CTA",        id: "cta-optimization-specialist",   first: false },
      ];

  for (const it of items) {
    const btn = document.createElement("button");
    btn.className = "quick-action" + (it.first ? " suggested" : "");
    btn.textContent = it.label;
    btn.addEventListener("click", () => {
      (document.getElementById("agent-select") as HTMLSelectElement).value = it.id;
      syncRunBtn();
    });
    wrap.appendChild(btn);
  }
  sec.style.display = "";
}

function renderScores(score?: ScoreResult): void {
  const el = $("#res-scores")!;
  el.innerHTML = "";
  if (!score) return;

  if (score.readability) {
    const g = score.readability.grade;
    const cls = g <= 6 ? "good" : g <= 10 ? "warn" : "bad";
    el.innerHTML += `<span class="score-badge ${cls}"><span class="dot"></span>Grade ${g}</span>`;
  }
  if (score.a11y) {
    const cls = score.a11y.passed ? "good" : "bad";
    const lbl = score.a11y.passed
      ? "A11y Pass"
      : `A11y: ${score.a11y.issues} issue${score.a11y.issues !== 1 ? "s" : ""}`;
    el.innerHTML += `<span class="score-badge ${cls}"><span class="dot"></span>${lbl}</span>`;
  }
}

function renderSuggestions(result: RunResult): void {
  const wrap = $("#res-suggestions")!;
  wrap.innerHTML = "";

  for (const s of result.suggestions) {
    const card = document.createElement("div");
    card.className = "suggestion-card" + (s.recommended ? " recommended" : "");
    card.innerHTML = `
      ${s.recommended ? '<div class="sug-label">Recommended</div>' : ""}
      <div class="sug-text">${esc(s.text)}</div>
      <div class="sug-reason">${esc(s.rationale)}</div>
      <div class="sug-actions">
        <button class="btn btn-success btn-sm js-apply" data-text="${escAttr(s.text)}">Apply</button>
        <button class="btn btn-secondary btn-sm js-copy" data-text="${escAttr(s.text)}">Copy</button>
      </div>`;
    wrap.appendChild(card);
  }

  // Bind apply buttons
  wrap.querySelectorAll(".js-apply").forEach(btn => {
    btn.addEventListener("click", () => {
      const text = (btn as HTMLElement).dataset.text || "";
      post({ type: "apply-text", text, nodeId });
    });
  });

  // Bind copy buttons
  wrap.querySelectorAll(".js-copy").forEach(btn => {
    btn.addEventListener("click", () => {
      const text = (btn as HTMLElement).dataset.text || "";
      navigator.clipboard.writeText(text).then(() => toast("Copied!"));
    });
  });
}

function showResults(result: RunResult, label: string, original: string): void {
  ($("#res-agent") as HTMLElement).textContent = label;
  ($("#res-original") as HTMLElement).textContent = original;
  ($("#res-full") as HTMLElement).textContent = result.content;
  renderSuggestions(result);
  renderScores(result.score);
  showScreen("results");
}

function renderHistory(): void {
  const list  = $("#hist-list")!;
  const empty = $("#hist-empty")!;
  list.innerHTML = "";

  if (!history.length) {
    empty.style.display = "flex";
    return;
  }
  empty.style.display = "none";

  for (const e of history) {
    const row = document.createElement("div");
    row.className = "history-row";
    row.innerHTML = `
      <span class="history-agent">${esc(e.agentLabel)}</span>
      <span class="history-text">${esc(e.originalText)}</span>
      <span class="history-time">${timeAgo(e.timestamp)}</span>`;
    row.addEventListener("click", () => showResults(e.result, e.agentLabel, e.originalText));
    list.appendChild(row);
  }
}

function syncRunBtn(): void {
  const btn = $("#btn-run") as HTMLButtonElement;
  const val = (document.getElementById("agent-select") as HTMLSelectElement).value;
  btn.disabled = !selection || !val;
}

function showError(msg: string): void {
  const el = $("#error-msg")!;
  el.textContent = msg;
  el.classList.add("visible");
  setTimeout(() => el.classList.remove("visible"), 5000);
}

// =====================================================================
// Run agent flow
// =====================================================================

async function handleRun(): Promise<void> {
  if (!selection) return;
  const agentId = (document.getElementById("agent-select") as HTMLSelectElement).value;
  if (!agentId) return;

  const preset   = (document.getElementById("preset-select") as HTMLSelectElement).value;
  const audience = (document.getElementById("in-audience") as HTMLInputElement).value.trim();
  const uiCtx    = (document.getElementById("in-context") as HTMLInputElement).value.trim();
  const tone     = (document.getElementById("in-tone") as HTMLInputElement).value.trim();
  const doScore  = (document.getElementById("chk-score") as HTMLInputElement).checked;

  const extra: Record<string, string> = {};
  if (audience) extra.target_audience = audience;
  if (uiCtx)    extra.ui_context = uiCtx;
  if (tone)     extra.tone = tone;

  const label = agentLabel(agentId);

  // Show loading
  ($("#load-agent") as HTMLElement).textContent = label;
  ($("#load-msg") as HTMLElement).textContent = `Running ${label}...`;
  showScreen("loading");

  try {
    const result = await callRunAgent(agentId, selection.text, preset, extra);

    // Optional auto-score on the first suggestion
    if (doScore && result.suggestions.length && !result.score) {
      try {
        result.score = await callScore(result.suggestions[0].text);
      } catch {
        // scoring is non-critical
      }
    }

    nodeId = selection.nodeId;

    pushHistory({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      agent: agentId,
      agentLabel: label,
      originalText: selection.text,
      result,
      preset,
      timestamp: Date.now(),
    });

    showResults(result, label, selection.text);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    showScreen("picker");
    showError(msg);
  }
}

// =====================================================================
// CSV export
// =====================================================================

function exportCSV(): void {
  if (!history.length) {
    toast("No history to export");
    return;
  }
  const hdr = ["Timestamp", "Agent", "Original", "Suggestion", "Preset"];
  const rows = history.map(e => [
    new Date(e.timestamp).toISOString(),
    e.agentLabel,
    `"${e.originalText.replace(/"/g, '""')}"`,
    `"${(e.result.suggestions[0]?.text || "").replace(/"/g, '""')}"`,
    e.preset || "",
  ]);
  const csv = [hdr.join(","), ...rows.map(r => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "cd-agency-history.csv";
  a.click();
  URL.revokeObjectURL(url);
  toast("Exported!");
}

// =====================================================================
// Wire up all event handlers
// =====================================================================

function bindEvents(): void {
  // --- Setup screen ---
  $("#btn-setup-save")!.addEventListener("click", () => {
    const url = (document.getElementById("setup-url") as HTMLInputElement).value.trim();
    const key = (document.getElementById("setup-key") as HTMLInputElement).value.trim();
    if (!url) { toast("Enter an API URL"); return; }
    saveSettings(url, key);
    showScreen("picker");
    post({ type: "get-selection" });
  });

  // --- Settings screen ---
  $("#btn-open-settings")!.addEventListener("click", () => {
    (document.getElementById("set-url") as HTMLInputElement).value = apiUrl;
    (document.getElementById("set-key") as HTMLInputElement).value = apiKey;
    showScreen("settings");
  });
  $("#btn-set-back")!.addEventListener("click", () => showScreen("picker"));
  $("#btn-set-save")!.addEventListener("click", () => {
    const url = (document.getElementById("set-url") as HTMLInputElement).value.trim();
    const key = (document.getElementById("set-key") as HTMLInputElement).value.trim();
    if (!url) { toast("Enter an API URL"); return; }
    saveSettings(url, key);
    toast("Settings saved");
    showScreen("picker");
  });

  // --- History screen ---
  $("#btn-open-history")!.addEventListener("click", () => { renderHistory(); showScreen("history"); });
  $("#btn-res-history")!.addEventListener("click",  () => { renderHistory(); showScreen("history"); });
  $("#btn-hist-back")!.addEventListener("click",    () => showScreen("picker"));
  $("#btn-hist-clear")!.addEventListener("click",   () => {
    history = [];
    saveHistory();
    renderHistory();
    toast("Cleared");
  });
  $("#btn-hist-export")!.addEventListener("click", exportCSV);

  // --- Collapsible toggles ---
  const togglePairs: [string, string][] = [["ctx-trigger", "ctx-body"], ["resp-trigger", "resp-body"]];
  for (const [trig, body] of togglePairs) {
    $(`#${trig}`)!.addEventListener("click", () => {
      $(`#${trig}`)!.classList.toggle("open");
      $(`#${body}`)!.classList.toggle("open");
    });
  }

  // --- Agent select ---
  document.getElementById("agent-select")!.addEventListener("change", syncRunBtn);

  // --- Run button ---
  $("#btn-run")!.addEventListener("click", handleRun);

  // --- Results navigation ---
  $("#btn-res-back")!.addEventListener("click",    () => showScreen("picker"));
  $("#btn-run-another")!.addEventListener("click", () => showScreen("picker"));
}

// =====================================================================
// Messages from code.ts (Figma sandbox)
// =====================================================================

function onPluginMessage(msg: PluginMsg): void {
  switch (msg.type) {
    case "selection": {
      const s = msg as SelectionMsg;
      selection = s;
      nodeId = s.nodeId;
      ($("#sel-text") as HTMLElement).textContent = s.text || "(empty)";
      ($("#sel-context") as HTMLElement).textContent =
        s.layerContext ? `${s.nodeName} in ${s.layerContext}` : s.nodeName;
      ($("#no-selection-overlay") as HTMLElement).style.display = "none";
      renderQuickActions(s.text);
      syncRunBtn();
      break;
    }
    case "no-selection": {
      const ns = msg as NoSelectionMsg;
      selection = null;
      ($("#sel-text") as HTMLElement).textContent = "No text layer selected";
      ($("#sel-context") as HTMLElement).textContent = "";
      ($("#no-selection-overlay") as HTMLElement).style.display = "flex";
      ($("#no-sel-reason") as HTMLElement).textContent = ns.reason;
      syncRunBtn();
      break;
    }
    case "apply-success":
      toast("Applied to layer!");
      break;
    case "apply-error":
      toast("Error: " + (msg as { type: string; error: string }).error);
      break;
  }
}

// =====================================================================
// Init
// =====================================================================

function init(): void {
  loadSettings();
  loadHistory();
  bindEvents();

  // Show setup on first launch, otherwise go straight to picker
  const configured = localStorage.getItem("cd-agency-url");
  showScreen(configured ? "picker" : "setup");

  if (!configured) {
    (document.getElementById("setup-url") as HTMLInputElement).value = DEFAULT_URL;
  }

  // Listen for messages from code.ts
  window.onmessage = (ev: MessageEvent) => {
    if (ev.data?.pluginMessage) onPluginMessage(ev.data.pluginMessage);
  };

  // Request current selection
  post({ type: "get-selection" });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
