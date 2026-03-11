import * as vscode from "vscode";
import * as api from "../api";
import { createScorePanel } from "../webview";

/**
 * Command handler: Score the currently selected text for readability,
 * accessibility, and lint quality.
 */
export async function scoreSelectionCommand(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("CD Agency: No active editor found.");
    return;
  }

  const selection = editor.selection;
  const selectedText = editor.document.getText(selection);

  if (!selectedText.trim()) {
    vscode.window.showWarningMessage(
      "CD Agency: Select some text to score."
    );
    return;
  }

  const result = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "CD Agency: Scoring selection...",
      cancellable: false,
    },
    async () => {
      try {
        return await api.scoreText(selectedText);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(message);
        return undefined;
      }
    }
  );

  if (!result) {
    return;
  }

  // Show a brief summary or open a detailed webview panel.
  const grade = result.readability.flesch_kincaid_grade;
  const ease = result.readability.ease_label;
  const lintFails = result.lint.failed_count;
  const a11yPass = result.a11y.passed ? "Pass" : "Fail";

  if (lintFails === 0 && result.a11y.issue_count === 0) {
    vscode.window.showInformationMessage(
      `CD Agency Score: Grade ${grade.toFixed(1)} (${ease}) | Lint: all passed | A11y: ${a11yPass}`
    );
  } else {
    createScorePanel(result, selectedText);
  }
}
