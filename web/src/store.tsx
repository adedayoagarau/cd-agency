import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type {
  AgentSummary,
  CombinedScore,
  ConversationMessage,
  Tab,
} from "./types";

interface StoreState {
  // Multi-provider support
  provider: string;
  setProvider: (p: string) => void;
  providerKeys: Record<string, string>;
  setProviderKey: (provider: string, key: string) => void;
  model: string;
  setModel: (m: string) => void;
  // Backward-compat alias
  apiKey: string;
  setApiKey: (key: string) => void;
  // Rest of state
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

function loadProviderKeys(): Record<string, string> {
  try {
    const raw = localStorage.getItem("cd-agency-provider-keys");
    if (raw) return JSON.parse(raw);
  } catch {}
  // Migrate from old single-key format
  const legacyKey = localStorage.getItem("cd-agency-api-key");
  if (legacyKey) return { anthropic: legacyKey };
  return {};
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [providerKeys, setProviderKeysState] = useState<Record<string, string>>(loadProviderKeys);
  const [provider, setProviderState] = useState(
    () => localStorage.getItem("cd-agency-provider") || "anthropic"
  );
  const [model, setModelState] = useState(
    () => localStorage.getItem("cd-agency-model") || ""
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

  const setProvider = useCallback((p: string) => {
    localStorage.setItem("cd-agency-provider", p);
    setProviderState(p);
  }, []);

  const setProviderKey = useCallback((prov: string, key: string) => {
    setProviderKeysState((prev) => {
      const next = { ...prev, [prov]: key };
      localStorage.setItem("cd-agency-provider-keys", JSON.stringify(next));
      // Also keep legacy key for backward compat
      if (prov === "anthropic") {
        localStorage.setItem("cd-agency-api-key", key);
      }
      return next;
    });
  }, []);

  const setModel = useCallback((m: string) => {
    localStorage.setItem("cd-agency-model", m);
    setModelState(m);
  }, []);

  // Backward-compat: apiKey is the key for the active provider
  const apiKey = providerKeys[provider] || "";
  const setApiKey = useCallback((key: string) => {
    setProviderKey(provider, key);
  }, [provider, setProviderKey]);

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
        provider, setProvider,
        providerKeys, setProviderKey,
        model, setModel,
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
