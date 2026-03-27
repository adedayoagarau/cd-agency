"use client";

import { Copy, Download, Send, Bookmark, Loader2 } from "lucide-react";
import { EvaluationChart } from "./evaluation-chart";
import type { RunResult } from "@/lib/api";

const demoDimensions = [
  { name: "Readability", score: 0.85 },
  { name: "Linter", score: 0.96 },
  { name: "Accessibility", score: 0.78 },
  { name: "Voice", score: 0.92 },
];

const demoCompositeScore = Math.round(
  (demoDimensions.reduce((sum, d) => sum + d.score, 0) / demoDimensions.length) * 100
);

interface AgentRunOutputProps {
  result?: RunResult | null;
  loading?: boolean;
  streamingContent?: string;
  streamingEvaluation?: Record<string, unknown> | null;
  streamingStatus?: "idle" | "running" | "done" | "error";
}

export function AgentRunOutput({ result, loading, streamingContent, streamingEvaluation, streamingStatus }: AgentRunOutputProps) {
  const isStreaming = streamingStatus === "running";
  const isStreamDone = streamingStatus === "done";

  // Loading state
  if (loading || (isStreaming && !streamingContent)) {
    return (
      <div className="bg-surface-card rounded-xl p-6 shadow-soft flex flex-col items-center justify-center min-h-[300px]">
        <Loader2 className="w-6 h-6 animate-spin text-brand-500 mb-3" />
        <p className="text-sm text-stone-500">
          {isStreaming ? "Starting agent..." : "Running agent..."}
        </p>
      </div>
    );
  }

  // Determine data source: streaming, API result, or demo fallback
  const hasStreamContent = isStreaming || (isStreamDone && !!streamingContent);
  const hasResult = hasStreamContent || !!result;
  const outputText = hasStreamContent
    ? streamingContent || ""
    : result
      ? result.output
      : "Choose your file \u2192 Upload";

  // Build evaluation from streaming or HTTP result
  const streamEvalEntries = isStreamDone && streamingEvaluation
    ? Object.entries(streamingEvaluation).filter(([k]) => k !== "type" && k !== "composite_score" && k !== "passed")
    : null;

  const compositeScore = isStreamDone && streamingEvaluation?.composite_score != null
    ? Math.round(Number(streamingEvaluation.composite_score) * 100)
    : result
      ? Math.round(result.composite_score * 100)
      : demoCompositeScore;

  const passed = isStreamDone && streamingEvaluation?.passed != null
    ? Boolean(streamingEvaluation.passed)
    : result
      ? result.passed
      : true;

  const dimensions = streamEvalEntries
    ? streamEvalEntries.map(([name, score]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        score: Number(score),
      }))
    : result
      ? Object.entries(result.evaluation).map(([name, score]) => ({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          score,
        }))
      : demoDimensions;

  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-stone-700">Output</h3>
        {!hasResult && (
          <span className="text-[10px] font-medium text-stone-400 bg-stone-100 rounded-full px-2 py-0.5">
            Demo
          </span>
        )}
      </div>

      {/* Output text */}
      <div className="bg-stone-50 rounded-lg p-4 mb-4">
        <p className="text-sm text-stone-800 leading-relaxed whitespace-pre-wrap">
          {outputText}
        </p>
      </div>

      {/* Evaluation section */}
      <div className="border-t border-stone-100 pt-4 mt-4">
        <div className="flex items-center gap-3 mb-4">
          <span className="font-serif text-3xl font-semibold text-stone-800">
            {compositeScore}%
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
              passed
                ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                : "bg-rose-50 text-rose-700 border-rose-100"
            }`}
          >
            {passed ? "Pass" : "Fail"}
          </span>
          {result && result.iterations > 1 && (
            <span className="text-xs text-stone-400">
              {result.iterations} iterations
            </span>
          )}
          {result && (
            <span className="text-xs text-stone-400">
              {(result.duration_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>

        <EvaluationChart dimensions={dimensions} />
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap items-center gap-2 mt-6">
        <button
          type="button"
          onClick={() => navigator.clipboard.writeText(outputText)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
        >
          <Copy className="w-3.5 h-3.5" />
          Copy
        </button>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Export
        </button>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
        >
          <Send className="w-3.5 h-3.5" />
          Send to CMS
        </button>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-brand-500 text-white hover:bg-brand-600 transition-colors"
        >
          <Bookmark className="w-3.5 h-3.5" />
          Save to Memory
        </button>
      </div>
    </div>
  );
}
