import * as vscode from "vscode";
import type { AgentResult, ScoreResult } from "./api";

/** Escape HTML entities to avoid XSS when injecting user content. */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Create a webview panel that shows agent results with a before/after
 * comparison and an "Apply" button that replaces the original selection.
 */
export function createResultPanel(
  result: AgentResult,
  editor: vscode.TextEditor,
  selection: vscode.Selection
): vscode.WebviewPanel {
  const panel = vscode.window.createWebviewPanel(
    "cdAgencyResult",
    `CD Agency: ${result.agent}`,
    vscode.ViewColumn.Beside,
    { enableScripts: true }
  );

  panel.webview.html = getResultHtml(result);

  // Handle messages from the webview (e.g. "Apply" button click).
  panel.webview.onDidReceiveMessage(async (message: { command: string }) => {
    if (message.command === "apply") {
      const success = await editor.edit((editBuilder) => {
        editBuilder.replace(selection, result.content);
      });
      if (success) {
        vscode.window.showInformationMessage(
          "CD Agency: Suggestion applied."
        );
        panel.dispose();
      } else {
        vscode.window.showErrorMessage(
          "CD Agency: Could not apply suggestion — the editor may have changed."
        );
      }
    }
  });

  return panel;
}

/**
 * Create a webview panel that shows scoring results.
 */
export function createScorePanel(
  result: ScoreResult,
  originalText: string
): vscode.WebviewPanel {
  const panel = vscode.window.createWebviewPanel(
    "cdAgencyScore",
    "CD Agency: Score",
    vscode.ViewColumn.Beside,
    { enableScripts: false }
  );

  panel.webview.html = getScoreHtml(result, originalText);
  return panel;
}

// ---------------------------------------------------------------------------
// HTML generators
// ---------------------------------------------------------------------------

function getResultHtml(result: AgentResult): string {
  return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CD Agency Result</title>
  <style>
    ${getBaseStyles()}
    .comparison {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin: 16px 0;
    }
    .panel {
      background: var(--vscode-editor-background, #1e1e1e);
      border: 1px solid var(--vscode-panel-border, #333);
      border-radius: 6px;
      padding: 12px;
    }
    .panel h3 {
      margin: 0 0 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      opacity: 0.7;
    }
    .panel pre {
      white-space: pre-wrap;
      word-wrap: break-word;
      margin: 0;
      font-family: var(--vscode-editor-font-family, monospace);
      font-size: var(--vscode-editor-font-size, 13px);
      line-height: 1.5;
    }
    .explanation {
      margin: 16px 0;
      padding: 12px;
      background: var(--vscode-textBlockQuote-background, #222);
      border-left: 3px solid var(--vscode-textLink-foreground, #3794ff);
      border-radius: 0 6px 6px 0;
    }
    .actions {
      margin-top: 16px;
      display: flex;
      gap: 8px;
    }
    button {
      padding: 8px 16px;
      font-size: 13px;
      cursor: pointer;
      border: none;
      border-radius: 4px;
      font-family: var(--vscode-font-family, sans-serif);
    }
    button.primary {
      background: var(--vscode-button-background, #0e639c);
      color: var(--vscode-button-foreground, #fff);
    }
    button.primary:hover {
      background: var(--vscode-button-hoverBackground, #1177bb);
    }
  </style>
</head>
<body>
  <h2>Agent: ${escapeHtml(result.agent)}</h2>

  <div class="comparison">
    <div class="panel">
      <h3>Before</h3>
      <pre>${escapeHtml(result.original)}</pre>
    </div>
    <div class="panel">
      <h3>After</h3>
      <pre>${escapeHtml(result.content)}</pre>
    </div>
  </div>

  <div class="actions">
    <button class="primary" id="applyBtn">Apply Suggestion</button>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    document.getElementById('applyBtn').addEventListener('click', () => {
      vscode.postMessage({ command: 'apply' });
    });
  </script>
</body>
</html>`;
}

function getScoreHtml(result: ScoreResult, originalText: string): string {
  const r = result.readability;
  const failedLintIssues = result.lint.issues.filter((i) => !i.passed);
  const a11yIssues = result.a11y.issues;

  const issueRows = [
    ...failedLintIssues.map(
      (i) => /* html */ `
      <tr>
        <td class="severity-${i.severity}">lint: ${escapeHtml(i.severity)}</td>
        <td>${escapeHtml(i.rule)}</td>
        <td>${escapeHtml(i.message)}</td>
        <td>${i.suggestion ? escapeHtml(i.suggestion) : "\u2014"}</td>
      </tr>`
    ),
    ...a11yIssues.map(
      (i) => /* html */ `
      <tr>
        <td class="severity-${i.severity}">a11y: ${escapeHtml(i.severity)}</td>
        <td>${escapeHtml(i.rule)}</td>
        <td>${escapeHtml(i.message)}</td>
        <td>${i.suggestion ? escapeHtml(i.suggestion) : "\u2014"}</td>
      </tr>`
    ),
  ].join("");

  const easePercent = Math.round(Math.max(0, Math.min(100, r.flesch_reading_ease)));

  return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CD Agency Score</title>
  <style>
    ${getBaseStyles()}
    .metric { margin: 8px 0; }
    .metric strong { display: inline-block; width: 180px; }
    .bar {
      height: 10px;
      background: var(--vscode-panel-border, #333);
      border-radius: 5px;
      overflow: hidden;
      margin-bottom: 24px;
    }
    .bar-fill {
      height: 100%;
      border-radius: 5px;
      background: var(--vscode-charts-green, #4caf50);
      width: ${easePercent}%;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
    }
    th, td {
      text-align: left;
      padding: 6px 10px;
      border-bottom: 1px solid var(--vscode-panel-border, #333);
      font-size: 13px;
    }
    th { opacity: 0.7; font-weight: 600; }
    .severity-error { color: var(--vscode-errorForeground, #f44); }
    .severity-warning { color: var(--vscode-editorWarning-foreground, #fa4); }
    .severity-info { color: var(--vscode-editorInfo-foreground, #3af); }
    .text-preview {
      background: var(--vscode-editor-background, #1e1e1e);
      border: 1px solid var(--vscode-panel-border, #333);
      border-radius: 6px;
      padding: 12px;
      white-space: pre-wrap;
      font-family: var(--vscode-editor-font-family, monospace);
      font-size: var(--vscode-editor-font-size, 13px);
      margin-bottom: 16px;
    }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
    .badge.pass { background: #1b5e20; color: #a5d6a7; }
    .badge.fail { background: #b71c1c; color: #ef9a9a; }
  </style>
</head>
<body>
  <h2>Content Score</h2>

  <div class="text-preview">${escapeHtml(originalText)}</div>

  <h3>Readability</h3>
  <div class="metric"><strong>Flesch Reading Ease:</strong> ${r.flesch_reading_ease.toFixed(1)} (${escapeHtml(r.ease_label)})</div>
  <div class="bar"><div class="bar-fill"></div></div>
  <div class="metric"><strong>Flesch-Kincaid Grade:</strong> ${r.flesch_kincaid_grade.toFixed(1)} (${escapeHtml(r.grade_label)})</div>
  <div class="metric"><strong>Word Count:</strong> ${r.word_count}</div>

  <h3>Lint</h3>
  <div class="metric">${result.lint.passed_count} passed, ${result.lint.failed_count} failed of ${result.lint.total_rules} rules</div>

  <h3>Accessibility <span class="badge ${result.a11y.passed ? "pass" : "fail"}">${result.a11y.passed ? "PASS" : "FAIL"}</span></h3>
  <div class="metric">${escapeHtml(result.a11y.label)} (${result.a11y.issue_count} issue${result.a11y.issue_count !== 1 ? "s" : ""})</div>

  ${
    failedLintIssues.length + a11yIssues.length > 0
      ? /* html */ `
  <h3>Issues (${failedLintIssues.length + a11yIssues.length})</h3>
  <table>
    <thead>
      <tr><th>Type</th><th>Rule</th><th>Message</th><th>Suggestion</th></tr>
    </thead>
    <tbody>${issueRows}</tbody>
  </table>`
      : "<p>No issues found.</p>"
  }
</body>
</html>`;
}

/** Shared CSS that picks up VS Code theme variables. */
function getBaseStyles(): string {
  return `
    body {
      font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, sans-serif);
      font-size: var(--vscode-font-size, 13px);
      color: var(--vscode-foreground, #ccc);
      background: var(--vscode-editor-background, #1e1e1e);
      padding: 16px;
      margin: 0;
    }
    h2 {
      margin: 0 0 12px;
      font-size: 18px;
      font-weight: 600;
    }
    h3 {
      margin: 20px 0 8px;
      font-size: 14px;
      font-weight: 600;
    }
  `;
}
