import * as vscode from "vscode";
import * as api from "./api";

/** Languages in which we attempt to extract string literals. */
const SUPPORTED_LANGUAGES = new Set([
  "javascript",
  "javascriptreact",
  "typescript",
  "typescriptreact",
  "json",
]);

/**
 * Represents a string literal extracted from a document,
 * with its text content and location.
 */
interface ExtractedString {
  text: string;
  range: vscode.Range;
}

/**
 * Extract string literals from JS/TS/JSX/TSX source text.
 *
 * This is a lightweight heuristic parser — it finds single- and double-quoted
 * strings as well as template literals (without interpolation) that are likely
 * user-facing content (length >= 3 characters, contains a space).
 */
function extractStringLiterals(
  document: vscode.TextDocument
): ExtractedString[] {
  const results: ExtractedString[] = [];
  const text = document.getText();
  // Match double-quoted, single-quoted, and simple backtick strings
  const stringPattern = /(?:"([^"\\]{3,}(?:\\.[^"\\]*)*)")|(?:'([^'\\]{3,}(?:\\.[^'\\]*)*)')|(?:`([^`$]{3,})`)/g;

  let match: RegExpExecArray | null;
  while ((match = stringPattern.exec(text)) !== null) {
    const content = match[1] ?? match[2] ?? match[3];
    if (!content || !content.includes(" ")) {
      continue; // skip non-prose strings (identifiers, paths, etc.)
    }

    // Determine the range for the string *content* (inside the quotes).
    const startOffset = match.index + 1; // skip opening quote
    const startPos = document.positionAt(startOffset);
    const endPos = document.positionAt(startOffset + content.length);
    results.push({ text: content, range: new vscode.Range(startPos, endPos) });
  }

  return results;
}

/**
 * Extract string values from a JSON document.
 */
function extractJsonStrings(
  document: vscode.TextDocument
): ExtractedString[] {
  const results: ExtractedString[] = [];
  const text = document.getText();
  // Match JSON string values (after a colon)
  const jsonValuePattern = /:\s*"([^"\\]{3,}(?:\\.[^"\\]*)*)"/g;

  let match: RegExpExecArray | null;
  while ((match = jsonValuePattern.exec(text)) !== null) {
    const content = match[1];
    if (!content || !content.includes(" ")) {
      continue;
    }
    const valueStart = match.index + match[0].indexOf('"') + 1;
    const startPos = document.positionAt(valueStart);
    const endPos = document.positionAt(valueStart + content.length);
    results.push({ text: content, range: new vscode.Range(startPos, endPos) });
  }

  return results;
}

/**
 * Map API severity string to VS Code DiagnosticSeverity.
 */
function toSeverity(severity: string): vscode.DiagnosticSeverity {
  switch (severity) {
    case "error":
      return vscode.DiagnosticSeverity.Error;
    case "warning":
      return vscode.DiagnosticSeverity.Warning;
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

/**
 * Run content linting diagnostics on a text document.
 *
 * Extracts string literals, sends them to the lint API, and populates the
 * diagnostics collection with any issues found.
 */
export async function updateDiagnostics(
  document: vscode.TextDocument,
  diagnosticCollection: vscode.DiagnosticCollection
): Promise<void> {
  if (!SUPPORTED_LANGUAGES.has(document.languageId)) {
    return;
  }

  const config = vscode.workspace.getConfiguration("cdAgency");
  if (!config.get<boolean>("autoLint", true)) {
    return;
  }

  const strings =
    document.languageId === "json"
      ? extractJsonStrings(document)
      : extractStringLiterals(document);

  if (strings.length === 0) {
    diagnosticCollection.delete(document.uri);
    return;
  }

  const diagnostics: vscode.Diagnostic[] = [];

  // Lint each extracted string. We batch-lint all strings to keep API calls
  // manageable; in production you would debounce and/or cache.
  for (const extracted of strings) {
    let lintResult: api.LintResult;
    try {
      lintResult = await api.lintText(extracted.text);
    } catch {
      // If the API is unreachable, silently skip rather than flooding errors.
      continue;
    }

    // Only report failed lint rules as diagnostics.
    const failedIssues = lintResult.issues.filter((i) => !i.passed);

    for (const issue of failedIssues) {
      // The lint API doesn't provide character offsets, so we highlight the
      // entire extracted string range for each failed rule.
      const diagnostic = new vscode.Diagnostic(
        extracted.range,
        `[cd-agency] ${issue.message}`,
        toSeverity(issue.severity)
      );
      diagnostic.source = "cd-agency";
      diagnostic.code = issue.rule;

      diagnostics.push(diagnostic);
    }
  }

  diagnosticCollection.set(document.uri, diagnostics);
}
