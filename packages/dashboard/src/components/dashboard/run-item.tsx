"use client";

import { Check, RefreshCw, X } from "lucide-react";

interface RunItemProps {
  agent: string;
  input: string;
  status: "passed" | "iterating" | "failed";
  score?: string;
  iteration?: string;
  time: string;
  isFirst?: boolean;
}

function StatusIcon({ status }: { status: RunItemProps["status"] }) {
  const base = "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0";

  switch (status) {
    case "passed":
      return (
        <div className={`${base} bg-emerald-50`}>
          <Check className="w-4 h-4 text-emerald-600" strokeWidth={2.5} />
        </div>
      );
    case "iterating":
      return (
        <div className={`${base} bg-amber-50 relative`}>
          <RefreshCw className="w-4 h-4 text-amber-600 animate-spin-slow" />
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-amber-400 rounded-full animate-pulse" />
        </div>
      );
    case "failed":
      return (
        <div className={`${base} bg-rose-50`}>
          <X className="w-4 h-4 text-rose-600" strokeWidth={2.5} />
        </div>
      );
  }
}

function ScoreBadge({ status, score }: { status: RunItemProps["status"]; score?: string }) {
  switch (status) {
    case "passed":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
          {score}
        </span>
      );
    case "iterating":
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-stone-100 text-stone-500 border border-stone-200 opacity-50">
          Processing
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-100">
          <X className="w-3 h-3" />
          Failed Gate
        </span>
      );
  }
}

export function RunItem({
  agent,
  input,
  status,
  score,
  iteration,
  time,
  isFirst,
}: RunItemProps) {
  return (
    <div
      className={`flex items-center justify-between py-3 px-2 -mx-2 rounded-lg cursor-pointer transition-colors ${
        status === "failed" ? "hover:bg-rose-50/50" : "hover:bg-stone-50"
      } ${!isFirst ? "border-t border-stone-100" : ""}`}
    >
      <div className="flex items-start gap-4 min-w-0 flex-1">
        <StatusIcon status={status} />
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <p className="text-sm font-medium text-stone-800">{agent}</p>
            {status === "iterating" && iteration && (
              <span className="text-[10px] uppercase font-bold text-amber-600 tracking-wider bg-amber-50 px-1.5 py-0.5 rounded">
                Iterating {iteration}
              </span>
            )}
          </div>
          <p className="text-xs text-stone-500 truncate max-w-[320px]">{input}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 flex-shrink-0 ml-3 text-right">
        <ScoreBadge status={status} score={score} />
        <span className="text-xs text-stone-400 w-16">{time}</span>
      </div>
    </div>
  );
}
