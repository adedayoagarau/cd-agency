import { useState, useEffect } from "react";
import { useStore } from "../store";
import { listProviders } from "../api";
import type { ProviderConfig } from "../types";

const FALLBACK_PROVIDERS: ProviderConfig[] = [
  { name: "anthropic", label: "Anthropic (Claude)", defaultModel: "claude-sonnet-4-20250514", models: ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"], key_placeholder: "sk-ant-..." },
  { name: "openai", label: "OpenAI", defaultModel: "gpt-4o", models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini", "o3-mini"], key_placeholder: "sk-..." },
  { name: "gemini", label: "Google Gemini", defaultModel: "gemini-2.0-flash", models: ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro", "gemini-1.5-flash"], key_placeholder: "AI..." },
  { name: "openrouter", label: "OpenRouter", defaultModel: "openrouter/auto", models: ["openrouter/auto", "anthropic/claude-sonnet-4-20250514", "openai/gpt-4o", "google/gemini-2.0-flash-001"], key_placeholder: "sk-or-..." },
  { name: "kimi", label: "KIMI (Moonshot)", defaultModel: "moonshot-v1-8k", models: ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"], key_placeholder: "sk-..." },
  { name: "ollama", label: "Ollama (Local)", defaultModel: "llama3", models: ["llama3", "llama3.1", "mistral", "codellama", "phi3", "gemma2"], key_placeholder: "(not required)" },
];

export function ApiKeyModal() {
  const { provider, setProvider, providerKeys, setProviderKey, model, setModel, apiKey } = useStore();
  const [open, setOpen] = useState(!apiKey);
  const [providers, setProviders] = useState<ProviderConfig[]>(FALLBACK_PROVIDERS);
  const [keyValue, setKeyValue] = useState(providerKeys[provider] || "");

  useEffect(() => {
    listProviders().then(setProviders).catch(() => {});
  }, []);

  useEffect(() => {
    setKeyValue(providerKeys[provider] || "");
  }, [provider, providerKeys]);

  if (!open) return null;

  const currentProvider = providers.find((p) => p.name === provider) || providers[0];
  const isOllama = provider === "ollama";

  return (
    <div className="modal-overlay">
      <div className="modal" style={{ maxWidth: 520 }}>
        <h2>LLM Provider Settings</h2>
        <p style={{ marginBottom: 16, opacity: 0.8 }}>
          Choose your LLM provider and enter your API key. Use any provider — Anthropic, OpenAI, Gemini, OpenRouter, KIMI, or a local Ollama instance.
        </p>

        {/* Provider selector */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
          {providers.map((p) => (
            <button
              key={p.name}
              className={`btn btn-sm ${provider === p.name ? "btn-primary" : ""}`}
              onClick={() => setProvider(p.name)}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* API Key input */}
        {!isOllama && (
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", marginBottom: 4, fontSize: 13, opacity: 0.7 }}>
              API Key for {currentProvider.label}
            </label>
            <input
              type="password"
              value={keyValue}
              onChange={(e) => setKeyValue(e.target.value)}
              placeholder={currentProvider.key_placeholder}
              className="input-full"
              autoFocus
            />
          </div>
        )}

        {isOllama && (
          <p style={{ fontSize: 13, opacity: 0.7, marginBottom: 12 }}>
            Ollama runs locally — no API key needed. Make sure Ollama is running on localhost:11434.
          </p>
        )}

        {/* Model selector */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", marginBottom: 4, fontSize: 13, opacity: 0.7 }}>
            Model
          </label>
          <select
            className="input-full"
            value={model || currentProvider.defaultModel}
            onChange={(e) => setModel(e.target.value)}
          >
            {currentProvider.models.map((m) => (
              <option key={m} value={m}>
                {m}{m === currentProvider.defaultModel ? " (default)" : ""}
              </option>
            ))}
          </select>
        </div>

        <div className="modal-actions">
          {apiKey && (
            <button className="btn" onClick={() => setOpen(false)}>Cancel</button>
          )}
          <button
            className="btn btn-primary"
            onClick={() => {
              if (!isOllama) setProviderKey(provider, keyValue);
              setOpen(false);
            }}
            disabled={!isOllama && !keyValue.trim()}
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}

export function ApiKeyButton() {
  const { provider, apiKey, providerKeys, setProvider, setProviderKey, model, setModel } = useStore();
  const [open, setOpen] = useState(false);
  const [providers] = useState<ProviderConfig[]>(FALLBACK_PROVIDERS);
  const [keyValue, setKeyValue] = useState(apiKey);

  useEffect(() => {
    setKeyValue(providerKeys[provider] || "");
  }, [provider, providerKeys]);

  const currentProvider = providers.find((p) => p.name === provider) || providers[0];
  const isOllama = provider === "ollama";
  const hasKey = isOllama || !!apiKey;

  return (
    <>
      <button
        className={`btn btn-sm ${hasKey ? "btn-success" : "btn-warn"}`}
        onClick={() => { setKeyValue(providerKeys[provider] || ""); setOpen(true); }}
        title={hasKey ? `${currentProvider.label} configured` : "No API key"}
      >
        {hasKey ? currentProvider.label : "Set Provider"}
      </button>
      {open && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 520 }}>
            <h2>LLM Provider Settings</h2>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
              {providers.map((p) => (
                <button
                  key={p.name}
                  className={`btn btn-sm ${provider === p.name ? "btn-primary" : ""}`}
                  onClick={() => setProvider(p.name)}
                >
                  {p.label}
                  {providerKeys[p.name] ? " *" : ""}
                </button>
              ))}
            </div>

            {!isOllama && (
              <input
                type="password"
                value={keyValue}
                onChange={(e) => setKeyValue(e.target.value)}
                placeholder={currentProvider.key_placeholder}
                className="input-full"
                autoFocus
              />
            )}

            {isOllama && (
              <p style={{ fontSize: 13, opacity: 0.7 }}>
                Ollama runs locally — no API key needed.
              </p>
            )}

            <div style={{ marginTop: 12 }}>
              <select
                className="input-full"
                value={model || currentProvider.defaultModel}
                onChange={(e) => setModel(e.target.value)}
              >
                {currentProvider.models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div className="modal-actions">
              <button className="btn" onClick={() => setOpen(false)}>Cancel</button>
              {!isOllama && apiKey && (
                <button className="btn btn-danger" onClick={() => { setProviderKey(provider, ""); setOpen(false); }}>
                  Clear Key
                </button>
              )}
              <button
                className="btn btn-primary"
                onClick={() => { if (!isOllama) setProviderKey(provider, keyValue); setOpen(false); }}
                disabled={!isOllama && !keyValue.trim()}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
