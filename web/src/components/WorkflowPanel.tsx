import { useState, useEffect } from "react";
import { useStore } from "../store";
import { listWorkflows, getWorkflow, runWorkflow } from "../api";
import type { WorkflowSummary, WorkflowDetail, WorkflowRunResponse } from "../types";

export function WorkflowPanel() {
  const { loading, setLoading, addTokens, setError } = useStore();
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selected, setSelected] = useState<WorkflowDetail | null>(null);
  const [input, setInput] = useState("");
  const [result, setResult] = useState<WorkflowRunResponse | null>(null);

  useEffect(() => {
    listWorkflows().then(setWorkflows).catch(() => {});
  }, []);

  const handleSelect = async (slug: string) => {
    try {
      const detail = await getWorkflow(slug);
      setSelected(detail);
      setResult(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleRun = async () => {
    if (!selected || !input.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await runWorkflow(selected.slug, { content: input });
      setResult(res);
      addTokens(res.total_tokens);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel workflow-panel">
      <div className="workflow-selector">
        <div className="sidebar-label">Select Workflow</div>
        <div className="workflow-list">
          {workflows.map((w) => (
            <button
              key={w.slug}
              className={`workflow-item ${selected?.slug === w.slug ? "active" : ""}`}
              onClick={() => handleSelect(w.slug)}
            >
              <span className="workflow-name">{w.name}</span>
              <span className="workflow-steps">{w.step_count} steps</span>
            </button>
          ))}
        </div>
      </div>

      {selected && (
        <div className="workflow-content">
          <div className="workflow-header">
            <h3>{selected.name}</h3>
            <p>{selected.description}</p>
          </div>

          <div className="workflow-steps-list">
            {selected.steps.map((step, i) => (
              <div key={i} className={`workflow-step ${result?.steps[i]?.skipped ? "skipped" : ""}`}>
                <span className="step-number">{i + 1}</span>
                <span className="step-name">{step.name}</span>
                <span className="step-agent">{step.agent}</span>
                {result?.steps[i] && !result.steps[i].skipped && (
                  <div className="step-output">{result.steps[i].output.slice(0, 200)}...</div>
                )}
              </div>
            ))}
          </div>

          <div className="workflow-input">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter content to process through the workflow..."
              rows={4}
              className="editor-textarea"
            />
            <button
              className="btn btn-primary"
              onClick={handleRun}
              disabled={!input.trim() || loading}
            >
              {loading ? "Running..." : "Run Workflow"}
            </button>
          </div>

          {result && (
            <div className="workflow-result">
              <div className="sidebar-label">Final Output</div>
              <div className="form-output-content">{result.final_output}</div>
              <div className="score-detail">
                Tokens: {result.total_tokens.toLocaleString()} |
                Time: {(result.latency_ms / 1000).toFixed(1)}s
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
