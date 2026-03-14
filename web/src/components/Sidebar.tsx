import { useState, useEffect } from "react";
import { useStore } from "../store";
import { listAgents, listPresets, searchAgents } from "../api";
import type { AgentSummary, PresetSummary, Tab } from "../types";

export function Sidebar() {
  const {
    agents, setAgents, selectedAgent, selectAgent,
    preset, setPreset, tab, setTab, setLoading, setError,
  } = useStore();
  const [search, setSearch] = useState("");
  const [filtered, setFiltered] = useState<AgentSummary[]>([]);
  const [presets, setPresets] = useState<PresetSummary[]>([]);

  useEffect(() => {
    listAgents().then(setAgents).catch(() => {});
    listPresets().then(setPresets).catch(() => {});
  }, [setAgents]);

  useEffect(() => {
    if (!search.trim()) {
      setFiltered(agents);
      return;
    }
    const q = search.toLowerCase();
    setFiltered(
      agents.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.description.toLowerCase().includes(q) ||
          a.tags.some((t) => t.includes(q))
      )
    );
  }, [search, agents]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "chat", label: "Chat" },
    { id: "form", label: "Form" },
    { id: "workflow", label: "Workflow" },
    { id: "batch", label: "Batch" },
    { id: "history", label: "History" },
    { id: "scrape", label: "Scrape" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <div className="sidebar-label">MODE</div>
        <div className="tab-bar">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`tab-btn ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">PRESET</div>
        {presets.map((p) => (
          <button
            key={p.filename}
            className={`sidebar-btn ${preset === p.name ? "active" : ""}`}
            onClick={() => setPreset(p.name)}
          >
            {preset === p.name ? "\u25CF " : "\u25CB "}{p.name}
          </button>
        ))}
      </div>

      <div className="sidebar-section sidebar-agents">
        <div className="sidebar-label">AGENTS</div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search agents..."
          className="sidebar-search"
        />
        <div className="agent-list">
          {filtered.map((a) => (
            <button
              key={a.slug}
              className={`agent-item ${selectedAgent?.slug === a.slug ? "active" : ""}`}
              onClick={() => selectAgent(a)}
            >
              <span className="agent-name">{a.name}</span>
              <span className="agent-tag">{a.tags[0] || "general"}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
