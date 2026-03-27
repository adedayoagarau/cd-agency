import { Activity } from "lucide-react";

const barHeights = [20, 40, 30, 60, 50, 80, 70, 90, 75, 10, 5, 2];
const barColors = [
  "bg-brand-200",
  "bg-brand-300",
  "bg-brand-200",
  "bg-brand-400",
  "bg-brand-300",
  "bg-brand-500",
  "bg-brand-400",
  "bg-brand-500",
  "bg-brand-400",
  "bg-stone-100",
  "bg-stone-100",
  "bg-stone-100",
];

export function UsageCard() {
  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft flex flex-col justify-between min-h-[180px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-400" />
          <span className="text-sm font-medium text-stone-600">Usage This Month</span>
        </div>
        <span className="text-xs text-stone-400">Resets in 12d</span>
      </div>

      {/* Value */}
      <div className="mb-3">
        <span className="text-3xl font-semibold text-stone-900">347</span>
        <span className="text-sm font-medium text-stone-400 ml-1">/ 500 runs</span>
      </div>

      {/* Sparkline */}
      <div className="flex items-end h-8 gap-[3px] mb-4" aria-hidden="true">
        {barHeights.map((height, i) => (
          <div
            key={i}
            className={`flex-1 rounded-sm ${barColors[i]}`}
            style={{ height: `${height}%` }}
          />
        ))}
      </div>

      {/* Progress bar */}
      <div className="flex items-center">
        <div className="flex-1 bg-brand-100 rounded-full h-1.5">
          <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: "69%" }} />
        </div>
        <span className="text-[10px] text-stone-400 ml-2 whitespace-nowrap font-medium">
          69%
        </span>
      </div>
    </div>
  );
}
