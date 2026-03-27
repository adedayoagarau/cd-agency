import type { MemoryStatsData } from "@/lib/api";

interface MemoryStatsProps {
  stats?: MemoryStatsData;
}

export function MemoryStats({ stats }: MemoryStatsProps) {
  const total = stats?.total_entries ?? 8;
  const session = stats?.session_count ?? 2;
  const project = stats?.project_count ?? 3;
  const workspace = stats?.workspace_count ?? 3;

  return (
    <div className="bg-surface-card rounded-xl p-5 shadow-soft">
      <h3 className="text-sm font-semibold text-stone-700 mb-4">
        Memory Stats
      </h3>

      {/* Stats list */}
      <div className="space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-stone-100">
          <span className="text-sm text-stone-500">Total entries</span>
          <span className="text-lg font-semibold text-stone-800">{total}</span>
        </div>
        <div className="flex items-center justify-between pb-3 border-b border-stone-100">
          <span className="text-sm text-stone-500">Session</span>
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-medium text-stone-700">{session}</span>
            <span className="text-[10px] text-stone-400">(TTL: 30m)</span>
          </div>
        </div>
        <div className="flex items-center justify-between pb-3 border-b border-stone-100">
          <span className="text-sm text-stone-500">Project</span>
          <span className="text-sm font-medium text-stone-700">{project}</span>
        </div>
        <div className="flex items-center justify-between pb-3 border-b border-stone-100">
          <span className="text-sm text-stone-500">Workspace</span>
          <span className="text-sm font-medium text-stone-700">{workspace}</span>
        </div>
      </div>

      {/* Storage bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-stone-400">Storage</span>
          <span className="text-xs text-stone-500">2.4 MB / 50 MB used</span>
        </div>
        <div className="w-full h-2 rounded-full bg-stone-100">
          <div
            className="h-2 rounded-full bg-brand-500"
            style={{ width: "5%" }}
          />
        </div>
      </div>

      {/* Clear session memory button */}
      <button
        type="button"
        className="mt-4 w-full text-sm text-rose-600 border border-rose-200 rounded-lg py-2 hover:bg-rose-50 transition-colors"
      >
        Clear session memory
      </button>
    </div>
  );
}
