"use client";

import { useState } from "react";
import { X, Eye, EyeOff, Copy, AlertTriangle } from "lucide-react";
import { setStoredKeys, type StoredKeys } from "@/lib/api-keys-store";

interface AddKeyDialogProps {
  open: boolean;
  onClose: () => void;
  type: "llm" | "workspace";
  providerName?: string;
  onSave?: () => void;
}

const PROVIDER_FIELD_MAP: Record<string, keyof StoredKeys> = {
  Anthropic: "anthropic",
  OpenAI: "openai",
  OpenRouter: "openrouter",
};

export function AddKeyDialog({ open, onClose, type, providerName, onSave }: AddKeyDialogProps) {
  const [keyName, setKeyName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [generatedKey, setGeneratedKey] = useState("");
  const [copied, setCopied] = useState(false);

  if (!open) return null;

  function handleGenerate() {
    const fake = `cda_${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 10)}`;
    setGeneratedKey(fake);
    setGenerated(true);
  }

  function handleCopy() {
    navigator.clipboard.writeText(generatedKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleSaveLLMKey() {
    if (!apiKey.trim() || !providerName) return;
    const field = PROVIDER_FIELD_MAP[providerName];
    if (field) {
      setStoredKeys({ [field]: apiKey.trim() });
    }
    onSave?.();
    handleClose();
  }

  function handleClose() {
    setKeyName("");
    setApiKey("");
    setShowKey(false);
    setGenerated(false);
    setGeneratedKey("");
    setCopied(false);
    onClose();
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl p-6 shadow-2xl w-full max-w-md relative">
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 text-stone-400 hover:text-stone-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {type === "workspace" ? (
          <>
            <h2 className="font-serif text-xl text-stone-900 mb-4">
              Generate API Key
            </h2>

            {!generated ? (
              <>
                <label className="block text-sm font-medium text-stone-700 mb-1.5">
                  Key name
                </label>
                <input
                  type="text"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="e.g., Production API"
                  className="w-full border border-stone-200 rounded-lg px-3 py-2 text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 mb-4"
                />
                <button
                  onClick={handleGenerate}
                  disabled={!keyName.trim()}
                  className="bg-brand-500 text-white w-full py-2.5 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Generate
                </button>
              </>
            ) : (
              <>
                <div className="font-mono bg-stone-50 p-3 rounded-lg border border-stone-200 text-sm text-stone-700 break-all flex items-start gap-2 mb-3">
                  <span className="flex-1">{generatedKey}</span>
                  <button
                    onClick={handleCopy}
                    className="flex-shrink-0 text-stone-400 hover:text-stone-600 transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                {copied && (
                  <p className="text-xs text-emerald-600 mb-2">Copied to clipboard</p>
                )}
                <div className="bg-amber-50 text-amber-700 rounded-lg p-3 text-sm flex items-start gap-2 mb-4">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>This key won&apos;t be shown again. Copy it now.</span>
                </div>
                <button
                  onClick={handleClose}
                  className="bg-brand-500 text-white w-full py-2.5 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors"
                >
                  Done
                </button>
              </>
            )}
          </>
        ) : (
          <>
            <h2 className="font-serif text-xl text-stone-900 mb-4">
              Add API Key
            </h2>

            {providerName && (
              <p className="text-sm text-stone-500 mb-4">{providerName}</p>
            )}

            <label className="block text-sm font-medium text-stone-700 mb-1.5">
              API Key
            </label>
            <div className="relative mb-4">
              <input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full border border-stone-200 rounded-lg px-3 py-2 pr-10 text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600 transition-colors"
              >
                {showKey ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>

            <button
              onClick={handleSaveLLMKey}
              disabled={!apiKey.trim()}
              className="bg-brand-500 text-white w-full py-2.5 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save
            </button>
          </>
        )}
      </div>
    </div>
  );
}
