"use client";

import { useState, useEffect } from "react";
import { Plus, Check } from "lucide-react";
import {
  getStoredKeys,
  removeStoredKey,
  maskKey,
  type StoredKeys,
} from "@/lib/api-keys-store";
import {
  cmsCredentials,
  workspaceKeys,
} from "@/lib/data/api-keys";
import { KeyRow } from "@/components/api-keys/key-row";
import { AddKeyDialog } from "@/components/api-keys/add-key-dialog";
import { api } from "@/lib/api";

export default function ApiKeysPage() {
  const [keys, setLocalKeys] = useState<StoredKeys>({});
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<"llm" | "workspace">("workspace");
  const [dialogProvider, setDialogProvider] = useState<string | undefined>();
  const [testStatus, setTestStatus] = useState<Record<string, "success" | "error" | null>>({});

  useEffect(() => {
    setLocalKeys(getStoredKeys());
  }, []);

  function refreshKeys() {
    setLocalKeys(getStoredKeys());
  }

  function openLLMDialog(providerName: string) {
    setDialogType("llm");
    setDialogProvider(providerName);
    setDialogOpen(true);
  }

  function openWorkspaceDialog() {
    setDialogType("workspace");
    setDialogProvider(undefined);
    setDialogOpen(true);
  }

  function handleRemove(provider: keyof StoredKeys) {
    removeStoredKey(provider);
    setLocalKeys(getStoredKeys());
    setTestStatus((prev) => ({ ...prev, [provider]: null }));
  }

  async function handleTest(provider: string) {
    try {
      await api.healthCheck();
      setTestStatus((prev) => ({ ...prev, [provider]: "success" }));
      setTimeout(() => setTestStatus((prev) => ({ ...prev, [provider]: null })), 3000);
    } catch {
      setTestStatus((prev) => ({ ...prev, [provider]: "error" }));
      setTimeout(() => setTestStatus((prev) => ({ ...prev, [provider]: null })), 3000);
    }
  }

  const llmProviders = [
    {
      id: "anthropic" as const,
      name: "Anthropic",
      connected: !!keys.anthropic,
      maskedKey: keys.anthropic ? maskKey(keys.anthropic) : null,
    },
    {
      id: "openai" as const,
      name: "OpenAI",
      connected: !!keys.openai,
      maskedKey: keys.openai ? maskKey(keys.openai) : null,
    },
    {
      id: "openrouter" as const,
      name: "OpenRouter",
      connected: !!keys.openrouter,
      maskedKey: keys.openrouter ? maskKey(keys.openrouter) : null,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">
          API Keys
        </h1>
        <p className="text-sm text-stone-500 mt-1">
          Manage your API keys and credentials for LLM providers, CMS platforms, and workspace access.
        </p>
      </div>

      {/* Section 1: LLM Providers */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h3 className="text-base font-semibold text-stone-900">
          LLM API Keys
        </h3>
        <p className="text-sm text-stone-500 mb-4">
          These keys are used by agents to generate content.
        </p>
        <div className="divide-y divide-stone-100">
          {llmProviders.map((provider) => (
            <div key={provider.id}>
              <KeyRow
                name={provider.name}
                connected={provider.connected}
                maskedKey={provider.maskedKey}
                lastUsed={null}
                onAdd={() => openLLMDialog(provider.name)}
                onEdit={() => openLLMDialog(provider.name)}
                onRemove={() => handleRemove(provider.id)}
                onTest={() => handleTest(provider.id)}
              />
              {testStatus[provider.id] === "success" && (
                <p className="text-xs text-emerald-600 px-4 pb-2">Connection successful</p>
              )}
              {testStatus[provider.id] === "error" && (
                <p className="text-xs text-rose-600 px-4 pb-2">Connection failed</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: CMS Credentials */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h3 className="text-base font-semibold text-stone-900">
          CMS Credentials
        </h3>
        <p className="text-sm text-stone-500 mb-4">
          Authentication for your connected content platforms.
        </p>
        <div className="divide-y divide-stone-100">
          {cmsCredentials.map((cred) => (
            <div key={cred.id} className="flex items-center gap-4 p-4">
              <div className="min-w-[100px]">
                <span className="text-sm font-medium text-stone-800">
                  {cred.platform}
                </span>
                <span className="block text-xs text-stone-400">{cred.type}</span>
              </div>
              <div className="flex items-center gap-3 flex-1">
                <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span className="font-mono text-xs text-stone-500 bg-stone-50 px-2 py-1 rounded">
                  {cred.maskedKey}
                </span>
                <span className="text-xs text-stone-400">
                  Last used: {cred.lastUsed}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button className="text-xs px-3 py-1 rounded-md border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors">
                  Test
                </button>
                <button className="text-xs px-3 py-1 rounded-md border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors">
                  Edit
                </button>
                <button className="text-xs text-rose-500 hover:text-rose-700 hover:bg-rose-50 px-3 py-1 rounded-md transition-colors">
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 3: Workspace API Keys */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-base font-semibold text-stone-900">API Keys</h3>
          <button
            onClick={openWorkspaceDialog}
            className="bg-brand-500 text-white text-sm px-4 py-2 rounded-lg font-medium hover:bg-brand-600 transition-colors inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Generate new key
          </button>
        </div>
        <p className="text-sm text-stone-500 mb-4">
          For programmatic access to your cd-agency workspace.
        </p>
        <div className="divide-y divide-stone-100">
          {workspaceKeys.map((key) => (
            <div key={key.id} className="flex items-center gap-4 p-4">
              <span className="text-sm font-medium text-stone-800 min-w-[120px]">
                {key.name}
              </span>
              <span className="font-mono text-xs text-stone-500 bg-stone-50 px-2 py-1 rounded">
                {key.maskedKey}
              </span>
              <span className="text-xs text-stone-400">
                Created: {key.created}
              </span>
              <span className="text-xs text-stone-400 flex-1">
                Last used: {key.lastUsed}
              </span>
              <button className="text-xs text-rose-500 hover:text-rose-700 hover:bg-rose-50 px-3 py-1 rounded-md transition-colors flex-shrink-0">
                Revoke
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Dialog */}
      <AddKeyDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        type={dialogType}
        providerName={dialogProvider}
        onSave={refreshKeys}
      />
    </div>
  );
}
