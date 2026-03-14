import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type {
  AgentSummary,
  CombinedScore,
  ConversationMessage,
  Tab,
} from "./types";

interface StoreState {
  apiKey: string;
  setApiKey: (key: string) => void;
  agents: AgentSummary[];
  setAgents: (agents: AgentSummary[]) => void;
  selectedAgent: AgentSummary | null;
  selectAgent: (agent: AgentSummary | null) => void;
  preset: string;
  setPreset: (p: string) => void;
  tab: Tab;
  setTab: (t: Tab) => void;
  messages: ConversationMessage[];
  addMessage: (msg: ConversationMessage) => void;
  clearMessages: () => void;
  scores: CombinedScore | null;
  setScores: (s: CombinedScore | null) => void;
  totalTokens: number;
  addTokens: (n: number) => void;
  loading: boolean;
  setLoading: (l: boolean) => void;
  error: string;
  setError: (e: string) => void;
}

const StoreContext = createContext<StoreState | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState(
    () => localStorage.getItem("cd-agency-api-key") || ""
  );
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [selectedAgent, selectAgent] = useState<AgentSummary | null>(null);
  const [preset, setPreset] = useState("default");
  const [tab, setTab] = useState<Tab>("chat");
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [scores, setScores] = useState<CombinedScore | null>(null);
  const [totalTokens, setTotalTokens] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const setApiKey = useCallback((key: string) => {
    localStorage.setItem("cd-agency-api-key", key);
    setApiKeyState(key);
  }, []);

  const addMessage = useCallback(
    (msg: ConversationMessage) => setMessages((prev) => [...prev, msg]),
    []
  );
  const clearMessages = useCallback(() => setMessages([]), []);
  const addTokens = useCallback(
    (n: number) => setTotalTokens((prev) => prev + n),
    []
  );

  return (
    <StoreContext.Provider
      value={{
        apiKey, setApiKey,
        agents, setAgents,
        selectedAgent, selectAgent,
        preset, setPreset,
        tab, setTab,
        messages, addMessage, clearMessages,
        scores, setScores,
        totalTokens, addTokens,
        loading, setLoading,
        error, setError,
      }}
    >
      {children}
    </StoreContext.Provider>
  );
}

export function useStore(): StoreState {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be inside StoreProvider");
  return ctx;
}
