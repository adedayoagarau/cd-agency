import * as vscode from "vscode";
import * as api from "../api";
import { createResultPanel } from "../webview";

/**
 * Command handler: Run a content design agent on the current editor selection.
 *
 * Flow:
 *  1. Grab the selected text from the active editor.
 *  2. Show a QuickPick so the user can choose an agent.
 *  3. Call the API and display results in a webview panel.
 */
export async function runAgentCommand(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("CD Agency: No active editor found.");
    return;
  }

  const selection = editor.selection;
  const selectedText = editor.document.getText(selection);

  if (!selectedText.trim()) {
    vscode.window.showWarningMessage(
      "CD Agency: Select some text before running an agent."
    );
    return;
  }

  // Fetch agents and let the user pick one.
  let agents: api.Agent[];
  try {
    agents = await api.listAgents();
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    vscode.window.showErrorMessage(message);
    return;
  }

  if (agents.length === 0) {
    vscode.window.showInformationMessage("CD Agency: No agents available.");
    return;
  }

  const picked = await vscode.window.showQuickPick(
    agents.map((a) => ({
      label: a.name,
      description: a.description,
      detail: a.tags.join(", "),
      slug: a.slug,
    })),
    {
      placeHolder: "Choose a content design agent",
      matchOnDescription: true,
      matchOnDetail: true,
    }
  );

  if (!picked) {
    return; // user cancelled
  }

  // Run the agent with a progress indicator.
  const result = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `CD Agency: Running "${picked.label}"...`,
      cancellable: false,
    },
    async () => {
      try {
        return await api.runAgent(picked.slug, selectedText);
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

  // Show the result in a webview panel with an "Apply" button.
  createResultPanel(result, editor, selection);
}
