import { Check, RefreshCw, X } from "lucide-react";
import { HistoryRun } from "@/lib/data/history";

interface HistoryRowProps {
  run: HistoryRun;
  onClick: () => void;
}

function StatusIcon({ status }: { status: HistoryRun["status"] }) {
  const base = "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0";

  switch (status) {
    case "passed":
      return (
        <div className={`${base} bg-emerald-50`}>
          <Check className="w-3.5 h-3.5 text-emerald-600" strokeWidth={2.5} />
        </div>
      );
    case "iterating":
      return (
        <div className={`${base} bg-amber-50`}>
          <RefreshCw className="w-3.5 h-3.5 text-amber-600 animate-spin" />
        </div>
      );
    case "failed":
      return (
        <div className={`${base} bg-rose-50`}>
          <X className="w-3.5 h-3.5 text-rose-600" strokeWidth={2.5} />
        </div>
      );
  }
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="text-xs text-stone-400">&mdash;</span>;
  }

  const pct = Math.round(score * 100);
  let classes: string;

  if (score >= 0.80) {
    classes = "bg-emerald-50 text-emerald-700";
  } else if (score >= 0.60) {
    classes = "bg-amber-50 text-amber-700";
  } else {
    classes = "bg-rose-50 text-rose-700";
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${classes}`}>
      {pct}%
    </span>
  );
}

export function HistoryRow({ run, onClick }: HistoryRowProps) {
  return (
    <tr
      onClick={onClick}
      className="hover:bg-stone-50 cursor-pointer transition-colors border-b border-stone-100 last:border-0"
    >
      <td className="py-3 px-4">
        <StatusIcon status={run.status} />
      </td>
      <td className="py-3 px-4">
        <span className="text-sm font-medium text-stone-800">{run.agent}</span>
      </td>
      <td className="py-3 px-4">
        <span className="text-sm text-stone-500 truncate block max-w-[200px]">{run.input}</span>
      </td>
      <td className="py-3 px-4">
        <ScoreBadge score={run.score} />
      </td>
      <td className="py-3 px-4">
        <span className="text-xs text-stone-400">{run.model}</span>
      </td>
      <td className="py-3 px-4">
        <span className="text-xs text-stone-400">{run.duration}</span>
      </td>
      <td className="py-3 px-4">
        <span className="text-xs text-stone-400">{run.time}</span>
      </td>
    </tr>
  );
}
