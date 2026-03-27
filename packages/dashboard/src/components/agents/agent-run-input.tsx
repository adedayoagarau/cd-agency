"use client";

import { useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { Agent } from "@/lib/data/agents";

interface AgentRunInputProps {
  agent: Agent;
  onRun: (input: string) => void;
  loading?: boolean;
}

const exampleInputs = [
  "Upload failed. Error code 413.",
  "Click here to manage your account settings and preferences.",
  "Are you sure you want to delete this? This action cannot be undone.",
];

export function AgentRunInput({ agent, onRun, loading }: AgentRunInputProps) {
  const [input, setInput] = useState("");
  const [model, setModel] = useState(agent.model);
  const [useCouncil, setUseCouncil] = useState(false);

  const handleRun = () => {
    if (!input.trim() || loading) return;
    onRun(input);
  };

  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft">
      <label
        htmlFor="agent-input"
        className="block text-sm font-medium text-stone-700 mb-2"
      >
        Input Content
      </label>
      <textarea
        id="agent-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Paste your content here..."
        className="w-full min-h-[200px] resize-y bg-white border border-stone-200 text-stone-800 rounded-lg px-4 py-3 text-sm leading-relaxed placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
      />

      {/* Options row */}
      <div className="flex items-center gap-4 mt-4">
        <div className="flex-1">
          <label
            htmlFor="model-select"
            className="block text-xs font-medium text-stone-500 mb-1"
          >
            Model
          </label>
          <select
            id="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full appearance-none bg-white border border-stone-200 text-stone-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="Claude 3.5 Sonnet">Claude 3.5 Sonnet</option>
            <option value="GPT-4o">GPT-4o</option>
            <option value="Claude 3 Opus">Claude 3 Opus</option>
          </select>
        </div>

        <div className="flex items-center gap-2 pt-4">
          <button
            type="button"
            role="switch"
            aria-checked={useCouncil}
            onClick={() => setUseCouncil(!useCouncil)}
            className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${
              useCouncil ? "bg-brand-500" : "bg-stone-300"
            }`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                useCouncil ? "translate-x-4" : "translate-x-0.5"
              }`}
            />
          </button>
          <span className="text-sm text-stone-600">Council</span>
        </div>
      </div>

      {/* Run button */}
      <button
        type="button"
        onClick={handleRun}
        disabled={loading || !input.trim()}
        className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-60 disabled:cursor-not-allowed text-white h-11 text-base font-medium rounded-md mt-4 transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Running...
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            Run Agent
          </>
        )}
      </button>

      {/* Example chips */}
      <div className="mt-4">
        <p className="text-xs text-stone-400 mb-2">Or try an example</p>
        <div className="flex flex-wrap gap-2">
          {exampleInputs.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setInput(example)}
              className="px-3 py-1.5 rounded-full text-xs font-medium bg-white border border-stone-200 text-stone-600 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50 transition-colors"
            >
              {example.length > 40 ? example.slice(0, 40) + "..." : example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
