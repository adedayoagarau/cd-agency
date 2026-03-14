import { useStore } from "../store";

export function StatusBar() {
  const { selectedAgent, preset, totalTokens, tab } = useStore();

  return (
    <footer className="status-bar">
      <span className="status-item">
        {selectedAgent ? selectedAgent.name : "No agent selected"}
      </span>
      <span className="status-separator">|</span>
      <span className="status-item">{preset}</span>
      <span className="status-separator">|</span>
      <span className="status-item">tokens: {totalTokens.toLocaleString()}</span>
      <span className="status-separator">|</span>
      <span className="status-item">mode: {tab}</span>
    </footer>
  );
}
