"use client";

import { ArrowUp, Pencil, Sparkles, Plus, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { useState } from "react";
import { useAgents, useRunAgent } from "@/lib/hooks";

const FALLBACK_AGENTS = [
  { slug: "microcopy-writer", name: "Microcopy Writer" },
  { slug: "brand-voice-evaluator", name: "Brand Voice Evaluator" },
  { slug: "seo-meta-generator", name: "SEO Meta Generator" },
  { slug: "error-message-crafter", name: "Error Message Crafter" },
  { slug: "tone-adjuster-formal", name: "Tone Adjuster (Formal)" },
];

const recentPrompts = [
  { label: '"Write a button label for file upload..."', type: "recent" as const },
  { label: '"Payment failed error message..."', type: "recent" as const },
  { label: "Suggested: Evaluate homepage hero", type: "suggested" as const },
];

export function QuickRunCard() {
  const [agent, setAgent] = useState("microcopy-writer");
  const [input, setInput] = useState("");

  const { data: agents } = useAgents();
  const { run, result, loading: runLoading, error: runError } = useRunAgent();

  const agentOptions = agents && agents.length > 0
    ? agents.map((a) => ({ slug: a.slug, name: a.name }))
    : FALLBACK_AGENTS;

  const handleRun = async () => {
    if (!input.trim() || runLoading) return;
    await run({ agent_slug: agent, content: input });
  };

  return (
    <div className="bg-surface-highlight rounded-xl p-6 md:p-8 shadow-sm-soft border border-stone-200/40">
      {/* Top row */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-serif text-xl md:text-2xl font-medium text-stone-900">
          Quick Run
        </h2>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-stone-200/60 text-xs font-medium text-stone-600">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          Claude 3.5 Sonnet
        </span>
      </div>

      <p className="text-sm text-stone-500 mb-5">
        Select an agent and paste content to evaluate or rewrite instantly.
      </p>

      {/* Input row */}
      <div className="flex flex-col md:flex-row gap-4">
        {/* Agent select */}
        <div className="md:w-1/3">
          <label
            htmlFor="agent-select"
            className="block text-xs font-medium text-stone-500 mb-1.5"
          >
            Select Agent
          </label>
          <select
            id="agent-select"
            value={agent}
            onChange={(e) => setAgent(e.target.value)}
            className="w-full appearance-none bg-white border border-stone-200 text-stone-800 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 shadow-sm"
          >
            {agentOptions.map((a) => (
              <option key={a.slug} value={a.slug}>
                {a.name}
              </option>
            ))}
          </select>
        </div>

        {/* Content input */}
        <div className="md:w-2/3">
          <label
            htmlFor="content-input"
            className="block text-xs font-medium text-stone-500 mb-1.5"
          >
            Input Content
          </label>
          <div className="relative">
            <textarea
              id="content-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Paste UI text, a paragraph, or a concept here..."
              rows={1}
              className="w-full resize-none min-h-[44px] bg-white border border-stone-200 text-stone-800 rounded-lg px-4 py-2.5 pr-28 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 shadow-sm"
            />
            <button
              type="button"
              disabled={runLoading || !input.trim()}
              onClick={handleRun}
              className="absolute bottom-2 right-2 inline-flex items-center gap-1.5 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-1.5 rounded-md text-sm font-medium transition-colors"
            >
              {runLoading ? (
                <>
                  Running...
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                </>
              ) : (
                <>
                  Run Agent
                  <ArrowUp className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
          {runError && (
            <p className="mt-2 text-sm text-red-600">{runError}</p>
          )}
        </div>
      </div>

      {/* Result section */}
      {result && (
        <div className="mt-5">
          <div className="bg-white rounded-lg p-4 border border-stone-200">
            <div className="flex items-center gap-2 mb-3">
              {result.passed ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-xs font-medium text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3" />
                  Passed
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-50 text-xs font-medium text-red-700 border border-red-200">
                  <XCircle className="w-3 h-3" />
                  Failed
                </span>
              )}
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-stone-100 text-xs font-medium text-stone-600">
                Score: {result.composite_score.toFixed(1)}
              </span>
            </div>
            <p className="text-sm text-stone-800 whitespace-pre-wrap">{result.output}</p>
          </div>
        </div>
      )}

      {/* Recent prompts */}
      <div className="border-t border-stone-200/60 mt-5 pt-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-stone-400 uppercase tracking-wider">
            Pick up where you left off
          </span>
          <a
            href="#"
            className="text-xs text-brand-600 hover:text-brand-700 transition-colors"
          >
            View all templates
          </a>
        </div>

        <div className="flex flex-wrap gap-2">
          {recentPrompts.map((prompt) => (
            <button
              key={prompt.label}
              type="button"
              onClick={() => setInput(prompt.label.replace(/^"|"$/g, ""))}
              className={
                prompt.type === "recent"
                  ? "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-white border border-stone-200 text-stone-600 hover:border-brand-300 hover:text-brand-700 hover:bg-brand-50 transition-colors"
                  : "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-brand-50 border border-brand-200 text-brand-700 hover:bg-brand-100 transition-colors"
              }
            >
              {prompt.type === "recent" ? (
                <Pencil className="w-3 h-3" />
              ) : (
                <Sparkles className="w-3 h-3" />
              )}
              {prompt.label}
            </button>
          ))}
          <button
            type="button"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border border-dashed border-stone-300 text-stone-400 hover:text-brand-500 hover:border-brand-300 hover:bg-brand-50 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Browse templates
          </button>
        </div>
      </div>
    </div>
  );
}
