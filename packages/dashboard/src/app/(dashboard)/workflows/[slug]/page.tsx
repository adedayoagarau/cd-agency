"use client";

import { use, useState } from "react";
import { GitBranch, Play, Loader2, CheckCircle, XCircle, ArrowDown } from "lucide-react";
import { useWorkflow, useRunWorkflow } from "@/lib/hooks";

export default function WorkflowDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { data: workflow, loading } = useWorkflow(slug);
  const { run, result, loading: running, error } = useRunWorkflow();
  const [input, setInput] = useState("");

  const handleRun = () => {
    if (!input.trim() || running) return;
    run(slug, { content: input });
  };

  const runResult = result as any;

  if (loading) {
    return <div className="text-sm text-stone-400 animate-pulse p-6">Loading workflow...</div>;
  }

  if (!workflow) {
    return <div className="text-sm text-stone-500 p-6">Workflow not found.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <GitBranch className="w-5 h-5 text-brand-500" />
          <h1 className="font-serif text-2xl font-semibold text-stone-900">{workflow.name}</h1>
        </div>
        <p className="text-stone-500">{workflow.description}</p>
      </div>

      {/* Pipeline visualization */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h2 className="text-sm font-semibold text-stone-700 mb-4">Pipeline Steps</h2>
        <div className="space-y-1">
          {workflow.steps?.map((step: any, i: number) => (
            <div key={i}>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-stone-50 border border-stone-200">
                <div className="w-6 h-6 rounded-full bg-brand-100 flex items-center justify-center text-xs font-bold text-brand-700">
                  {i + 1}
                </div>
                <div>
                  <p className="text-sm font-medium text-stone-800">{step.name}</p>
                  <p className="text-xs text-stone-500">Agent: {step.agent}</p>
                </div>
                {runResult?.steps?.[i] && (
                  <div className="ml-auto">
                    {runResult.steps[i].skipped ? (
                      <span className="text-xs text-stone-400">Skipped</span>
                    ) : runResult.steps[i].error ? (
                      <XCircle className="w-4 h-4 text-rose-500" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-emerald-500" />
                    )}
                  </div>
                )}
              </div>
              {i < (workflow.steps?.length ?? 0) - 1 && (
                <div className="flex justify-center py-0.5">
                  <ArrowDown className="w-4 h-4 text-stone-300" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Run input */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h2 className="text-sm font-semibold text-stone-700 mb-3">Run Workflow</h2>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter the content to process through this workflow..."
          rows={4}
          className="w-full bg-white border border-stone-200 rounded-lg px-4 py-3 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 mb-3"
        />
        <button
          onClick={handleRun}
          disabled={running || !input.trim()}
          className="inline-flex items-center gap-1.5 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {running ? "Running..." : "Run Workflow"}
        </button>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {/* Results */}
      {runResult && (
        <div className="bg-surface-card rounded-xl p-6 shadow-soft">
          <h2 className="text-sm font-semibold text-stone-700 mb-3">Output</h2>
          <div className="bg-stone-50 rounded-lg p-4 mb-4">
            <p className="text-sm text-stone-800 whitespace-pre-wrap">{runResult.final_output}</p>
          </div>
          <div className="flex items-center gap-4 text-xs text-stone-400">
            <span>Tokens: {runResult.total_tokens}</span>
            <span>Duration: {(runResult.latency_ms / 1000).toFixed(1)}s</span>
          </div>
        </div>
      )}
    </div>
  );
}
