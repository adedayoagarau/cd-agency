import { useState, useEffect } from "react";
import { useStore } from "../store";
import { listHistory } from "../api";
import type { VersionEntry } from "../types";

export function HistoryPanel() {
  const { setError } = useStore();
  const [entries, setEntries] = useState<VersionEntry[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    listHistory(50)
      .then(setEntries)
      .catch((err) => setError(err.message));
  }, [setError]);

  const toggle = (id: string) => {
    setExpanded(expanded === id ? null : id);
  };

  const fmt = (ts: number) => {
    const d = new Date(ts * 1000);
    return d.toLocaleString();
  };

  if (entries.length === 0) {
    return (
      <div className="panel history-panel">
        <div className="empty-state">No version history yet. Run an agent to create entries.</div>
      </div>
    );
  }

  return (
    <div className="panel history-panel">
      <div className="history-header">
        <h3>Version History</h3>
        <span className="history-count">{entries.length} entries</span>
      </div>
      <div className="history-timeline">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className={`history-entry ${expanded === entry.id ? "expanded" : ""}`}
          >
            <button className="history-entry-header" onClick={() => toggle(entry.id)}>
              <span className="history-dot" />
              <span className="history-agent">{entry.agent_name}</span>
              <span className="history-time">{fmt(entry.timestamp)}</span>
              <span className="history-tokens">
                {(entry.input_tokens + entry.output_tokens).toLocaleString()} tok
              </span>
            </button>
            {expanded === entry.id && (
              <div className="history-diff">
                <div className="history-diff-section">
                  <div className="diff-label">Input</div>
                  <div className="diff-before">{entry.input_text}</div>
                </div>
                <div className="history-diff-section">
                  <div className="diff-label">Output</div>
                  <div className="diff-after">{entry.output_text}</div>
                </div>
                <div className="score-detail">
                  Model: {entry.model} | Latency: {(entry.latency_ms / 1000).toFixed(1)}s
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
