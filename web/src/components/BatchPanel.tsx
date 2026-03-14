import { useState } from "react";
import { useStore } from "../store";
import { batchRunAgent } from "../api";
import type { AgentRunResponse } from "../types";

export function BatchPanel() {
  const { selectedAgent, loading, setLoading, addTokens, setError } = useStore();
  const [input, setInput] = useState("");
  const [results, setResults] = useState<AgentRunResponse[]>([]);

  const handleRun = async () => {
    if (!selectedAgent || !input.trim()) return;
    setLoading(true);
    setError("");
    setResults([]);

    // Split by double newline or --- separator
    const items = input
      .split(/\n{2,}|^---$/m)
      .map((s) => s.trim())
      .filter(Boolean);

    const primaryInput = selectedAgent.slug.includes("error")
      ? "error_message"
      : "content";

    try {
      const res = await batchRunAgent(
        selectedAgent.slug,
        items.map((text) => ({ input: { [primaryInput]: text } }))
      );
      setResults(res);
      const totalTok = res.reduce(
        (sum, r) => sum + r.input_tokens + r.output_tokens, 0
      );
      addTokens(totalTok);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCsvUpload = () => {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".csv,.txt";
    fileInput.onchange = async () => {
      const file = fileInput.files?.[0];
      if (file) {
        const text = await file.text();
        setInput(text);
      }
    };
    fileInput.click();
  };

  return (
    <div className="panel batch-panel">
      <div className="batch-header">
        <h3>Batch Processing</h3>
        <p>
          Enter multiple content items separated by blank lines.
          {selectedAgent
            ? ` Each will be processed by ${selectedAgent.name}.`
            : " Select an agent first."}
        </p>
      </div>

      <div className="batch-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={"Error: Connection timed out\n\nError: File not found\n\nError: Permission denied"}
          rows={8}
          className="editor-textarea"
        />
        <div className="batch-actions">
          <button className="btn btn-sm" onClick={handleCsvUpload}>Upload File</button>
          <button
            className="btn btn-primary"
            onClick={handleRun}
            disabled={!selectedAgent || !input.trim() || loading}
          >
            {loading ? "Processing..." : `Run Batch (${input.split(/\n{2,}|^---$/m).filter((s) => s.trim()).length} items)`}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="batch-results">
          <div className="sidebar-label">Results ({results.length})</div>
          {results.map((r, i) => (
            <div key={i} className="batch-result-item">
              <div className="batch-result-header">Item {i + 1} — {r.agent_name}</div>
              <div className="batch-result-content">{r.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
