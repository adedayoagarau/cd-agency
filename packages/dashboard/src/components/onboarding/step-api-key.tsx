"use client";

import { useState } from "react";
import { Eye, EyeOff, Check, ChevronDown, ChevronUp, X } from "lucide-react";
import { setStoredKeys, getStoredKeys } from "@/lib/api-keys-store";
import { api } from "@/lib/api";

interface StepApiKeyProps {
  onNext: () => void;
  onBack: () => void;
}

export function StepApiKey({ onNext, onBack }: StepApiKeyProps) {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [testPassed, setTestPassed] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);
  const [showMore, setShowMore] = useState(false);
  const [showWhy, setShowWhy] = useState(false);
  const [openAiKey, setOpenAiKey] = useState("");
  const [openRouterKey, setOpenRouterKey] = useState("");

  async function handleTestConnection() {
    if (!apiKey.trim()) return;
    setTesting(true);
    setTestError(null);
    // Save the key first so the API client picks it up
    setStoredKeys({ anthropic: apiKey.trim() });
    try {
      await api.healthCheck();
      setTestPassed(true);
    } catch (err) {
      setTestError(err instanceof Error ? err.message : "Connection failed");
      // Keep the key saved even if the test fails
    } finally {
      setTesting(false);
    }
  }

  function handleContinue() {
    // Save any optional keys on continue
    if (openAiKey.trim()) {
      setStoredKeys({ openai: openAiKey.trim() });
    }
    if (openRouterKey.trim()) {
      setStoredKeys({ openrouter: openRouterKey.trim() });
    }
    onNext();
  }

  return (
    <div className="flex flex-col">
      <h1 className="font-serif text-2xl text-center text-stone-900">
        Bring your own AI
      </h1>
      <p className="text-stone-500 text-center mt-2 mb-6">
        cd-agency uses your API keys to run agents. You control the costs.
      </p>

      {/* Anthropic API Key */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1.5">
          <label htmlFor="anthropic-key" className="text-sm font-medium text-stone-700">
            Anthropic API Key (required)
          </label>
          <a
            href="https://console.anthropic.com/settings/keys"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 hover:text-brand-700"
          >
            Get a key
          </a>
        </div>
        <div className="relative">
          <input
            id="anthropic-key"
            type={showKey ? "text" : "password"}
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value);
              setTestPassed(false);
              setTestError(null);
            }}
            placeholder="sk-ant-..."
            className="w-full h-11 rounded-lg border border-stone-200 bg-white px-3 pr-10 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-colors"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
            aria-label={showKey ? "Hide API key" : "Show API key"}
          >
            {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
      </div>

      {/* Test Connection */}
      <button
        onClick={handleTestConnection}
        disabled={!apiKey.trim() || testing}
        className="w-full py-2 mt-2 rounded-lg border border-brand-200 text-brand-600 text-sm font-medium hover:bg-brand-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {testing ? "Testing..." : "Test Connection"}
      </button>

      {testPassed && (
        <div className="flex items-center justify-center gap-2 mt-2 text-sm text-emerald-600">
          <Check size={16} />
          <span>Connected successfully</span>
        </div>
      )}

      {testError && (
        <div className="flex items-center justify-center gap-2 mt-2 text-sm text-rose-600">
          <X size={16} />
          <span>{testError}</span>
        </div>
      )}

      {/* Add more providers */}
      <button
        type="button"
        onClick={() => setShowMore(!showMore)}
        className="flex items-center justify-center gap-1 text-sm text-brand-600 cursor-pointer mt-4"
      >
        Add more providers
        {showMore ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      <div
        className={[
          "overflow-hidden transition-all duration-300",
          showMore ? "max-h-60 opacity-100 mt-3" : "max-h-0 opacity-0",
        ].join(" ")}
      >
        <div className="space-y-3">
          <div>
            <label htmlFor="openai-key" className="block text-sm font-medium text-stone-700 mb-1.5">
              OpenAI API Key
            </label>
            <input
              id="openai-key"
              type="password"
              value={openAiKey}
              onChange={(e) => setOpenAiKey(e.target.value)}
              onBlur={() => {
                if (openAiKey.trim()) setStoredKeys({ openai: openAiKey.trim() });
              }}
              placeholder="sk-..."
              className="w-full h-11 rounded-lg border border-stone-200 bg-white px-3 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-colors"
            />
          </div>
          <div>
            <label htmlFor="openrouter-key" className="block text-sm font-medium text-stone-700 mb-1.5">
              OpenRouter API Key
            </label>
            <input
              id="openrouter-key"
              type="password"
              value={openRouterKey}
              onChange={(e) => setOpenRouterKey(e.target.value)}
              onBlur={() => {
                if (openRouterKey.trim()) setStoredKeys({ openrouter: openRouterKey.trim() });
              }}
              placeholder="sk-or-..."
              className="w-full h-11 rounded-lg border border-stone-200 bg-white px-3 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Why do I need this? */}
      <button
        type="button"
        onClick={() => setShowWhy(!showWhy)}
        className="text-xs text-stone-400 hover:text-stone-600 mt-4 text-left cursor-pointer"
      >
        Why do I need this?
      </button>
      <div
        className={[
          "overflow-hidden transition-all duration-300",
          showWhy ? "max-h-40 opacity-100 mt-2" : "max-h-0 opacity-0",
        ].join(" ")}
      >
        <p className="text-xs text-stone-500 leading-relaxed">
          cd-agency sends prompts to AI providers on your behalf. By using your own API keys,
          you maintain full control over costs, rate limits, and data privacy. Your keys are
          stored locally in your browser. We never share them with third parties.
        </p>
      </div>

      {/* Continue */}
      <button
        onClick={handleContinue}
        disabled={!testPassed}
        className="bg-brand-500 text-white w-full h-11 rounded-xl mt-4 text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Continue
      </button>

      {/* Back */}
      <button
        onClick={onBack}
        className="text-sm text-stone-400 hover:text-stone-600 text-center mt-3 transition-colors"
      >
        Back
      </button>
    </div>
  );
}
