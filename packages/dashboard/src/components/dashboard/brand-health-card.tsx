import { Sparkles, ChevronUp } from "lucide-react";

export function BrandHealthCard() {
  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft flex flex-col justify-between min-h-[180px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-brand-500" />
          <span className="text-sm font-medium text-stone-600">Brand Health</span>
        </div>
        <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full bg-emerald-50 text-xs font-medium text-emerald-700">
          <ChevronUp className="w-3 h-3" />
          +2.4% this week
        </span>
      </div>

      {/* Value */}
      <div className="mb-3">
        <span className="font-serif text-4xl font-semibold text-stone-900">87</span>
        <span className="text-2xl text-stone-400">%</span>
      </div>

      {/* Context */}
      <p className="text-sm text-stone-500 mb-4">
        <span className="font-medium text-stone-600">Voice consistency</span> across 42 runs this week
      </p>

      {/* Progress bar */}
      <div
        className="bg-brand-100 rounded-full h-1.5"
        role="progressbar"
        aria-valuenow={87}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: "87%" }} />
      </div>
    </div>
  );
}
