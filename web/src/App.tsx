import { useEffect } from "react";
import { useStore } from "./store";
import { listAgents } from "./api";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { ChatPanel } from "./components/ChatPanel";
import { FormPanel } from "./components/FormPanel";
import { ScoringPanel } from "./components/ScoringPanel";
import { WorkflowPanel } from "./components/WorkflowPanel";
import { BatchPanel } from "./components/BatchPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { ScrapePanel } from "./components/ScrapePanel";
import { StatusBar } from "./components/StatusBar";
import { ApiKeyModal } from "./components/ApiKeyModal";

function CenterPanel() {
  const { tab } = useStore();
  switch (tab) {
    case "chat":
      return <ChatPanel />;
    case "form":
      return <FormPanel />;
    case "workflow":
      return <WorkflowPanel />;
    case "batch":
      return <BatchPanel />;
    case "history":
      return <HistoryPanel />;
    case "scrape":
      return <ScrapePanel />;
    default:
      return <ChatPanel />;
  }
}

export default function App() {
  const { apiKey, setAgents, error, setError } = useStore();

  useEffect(() => {
    listAgents().then(setAgents).catch(() => {});
  }, [setAgents]);

  return (
    <div className="app">
      <Header />
      {!apiKey && <ApiKeyModal />}
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button className="btn btn-sm" onClick={() => setError("")}>Dismiss</button>
        </div>
      )}
      <div className="app-body">
        <Sidebar />
        <main className="center-panel">
          <CenterPanel />
        </main>
        <ScoringPanel />
      </div>
      <StatusBar />
    </div>
  );
}
