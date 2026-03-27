"use client";

import { X, RefreshCw, Copy, Download } from "lucide-react";
import { HistoryRun } from "@/lib/data/history";
import { api } from "@/lib/api";

interface RunDetailSheetProps {
  run: HistoryRun | null;
  onClose: () => void;
}

function getBarColor(score: number): string {
  if (score >= 0.80) return "bg-emerald-500";
  if (score >= 0.60) return "bg-amber-500";
  return "bg-rose-500";
}

function StatusBadge({ status }: { status: HistoryRun["status"] }) {
  switch (status) {
    case "passed":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
          Passed
        </span>
      );
    case "iterating":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
          Iterating
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-100">
          Failed
        </span>
      );
  }
}

export function RunDetailSheet({ run, onClose }: RunDetailSheetProps) {
  if (!run) return null;

  const dimensions = run.evaluation
    ? [
        { name: "Readability", score: run.evaluation.readability },
        { name: "Linter", score: run.evaluation.linter },
        { name: "Accessibility", score: run.evaluation.accessibility },
        { name: "Voice", score: run.evaluation.voice },
      ]
    : [];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />

      {/* Panel */}
      <div className="fixed inset-y-0 right-0 w-[480px] bg-white shadow-2xl z-50 flex flex-col overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <h2 className="font-serif text-lg font-semibold text-stone-800">{run.agent}</h2>
            <StatusBadge status={run.status} />
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Meta info */}
        <div className="px-6 pt-4 pb-2 flex flex-wrap items-center gap-4 text-xs text-stone-400">
          <span>{run.model}</span>
          <span>{run.duration}</span>
          <span>{run.time}</span>
          {run.iterations && <span>{run.iterations} iteration{run.iterations > 1 ? "s" : ""}</span>}
        </div>

        {/* Full input */}
        <div className="px-6 py-4">
          <h3 className="text-sm font-medium text-stone-700 mb-2">Full Input</h3>
          <div className="bg-stone-50 rounded-lg p-4">
            <p className="text-sm text-stone-700 leading-relaxed">{run.input}</p>
          </div>
        </div>

        {/* Output */}
        <div className="px-6 py-4">
          <h3 className="text-sm font-medium text-stone-700 mb-2">Output</h3>
          <div className="bg-stone-50 rounded-lg p-4">
            <p className="text-sm text-stone-700 leading-relaxed whitespace-pre-wrap">{run.output}</p>
          </div>
        </div>

        {/* Evaluation */}
        {dimensions.length > 0 && (
          <div className="px-6 py-4 border-t border-stone-100">
            <h3 className="text-sm font-medium text-stone-700 mb-3">Evaluation</h3>
            {run.score !== null && (
              <div className="flex items-center gap-3 mb-4">
                <span className="font-serif text-3xl font-semibold text-stone-800">
                  {Math.round(run.score * 100)}%
                </span>
                <StatusBadge status={run.status} />
              </div>
            )}
            <div className="space-y-3">
              {dimensions.map((dim) => (
                <div key={dim.name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-stone-600">{dim.name}</span>
                    <span className="text-xs font-medium text-stone-500">
                      {Math.round(dim.score * 100)}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-stone-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${getBarColor(dim.score)} transition-all`}
                      style={{ width: `${Math.round(dim.score * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="px-6 py-4 mt-auto border-t border-stone-100">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Re-run
            </button>
            <button
              type="button"
              onClick={() => {
                if (run.output) {
                  navigator.clipboard.writeText(run.output);
                }
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              Copy output
            </button>
            <button
              type="button"
              onClick={async () => {
                try {
                  const entries = [{
                    source: run.input || run.agent,
                    target: run.output || `Score: ${run.score}`,
                    agent: run.agent,
                    context: run.time,
                  }];
                  const content = await api.exportContent(entries, "json");
                  const blob = new Blob([content], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `run-${run.id}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                } catch (e) {
                  console.error("Export failed:", e);
                }
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Export
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
