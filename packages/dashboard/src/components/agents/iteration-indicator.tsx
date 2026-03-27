"use client";

interface IterationIndicatorProps {
  current: number;
  total: number;
  label: string;
}

export function IterationIndicator({ current, total, label }: IterationIndicatorProps) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-xs font-medium text-amber-700">
      Iteration {current}/{total} — {label}
    </span>
  );
}
