"use client";

interface Dimension {
  name: string;
  score: number;
}

interface EvaluationChartProps {
  dimensions: Dimension[];
}

function getBarColor(score: number): string {
  if (score >= 0.80) return "bg-emerald-500";
  if (score >= 0.60) return "bg-amber-500";
  return "bg-rose-500";
}

export function EvaluationChart({ dimensions }: EvaluationChartProps) {
  return (
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
  );
}
