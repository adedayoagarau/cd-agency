"use client";

import { useState, useMemo } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import { HistoryRun } from "@/lib/data/history";
import { HistoryRow } from "./history-row";

interface HistoryTableProps {
  runs: HistoryRun[];
  onSelectRun: (run: HistoryRun) => void;
}

type SortField = "score" | "time";
type SortDir = "asc" | "desc";

const PAGE_SIZE = 15;

export function HistoryTable({ runs, onSelectRun }: HistoryTableProps) {
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(0);

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
    setPage(0);
  }

  const sorted = useMemo(() => {
    if (!sortField) return runs;

    return [...runs].sort((a, b) => {
      let cmp = 0;
      if (sortField === "score") {
        const aScore = a.score ?? -1;
        const bScore = b.score ?? -1;
        cmp = aScore - bScore;
      } else {
        // Sort by original order index as proxy for time
        cmp = runs.indexOf(a) - runs.indexOf(b);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [runs, sortField, sortDir]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const paginated = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const showingFrom = page * PAGE_SIZE + 1;
  const showingTo = Math.min((page + 1) * PAGE_SIZE, sorted.length);

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) {
      return <ChevronDown className="w-3 h-3 text-stone-300" />;
    }
    return sortDir === "asc" ? (
      <ChevronUp className="w-3 h-3 text-brand-600" />
    ) : (
      <ChevronDown className="w-3 h-3 text-brand-600" />
    );
  }

  return (
    <div className="bg-surface-card rounded-xl shadow-soft overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-stone-50/50">
              <th className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4 w-12">
                Status
              </th>
              <th className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4">
                Agent
              </th>
              <th className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4">
                Input
              </th>
              <th
                className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4 cursor-pointer select-none"
                onClick={() => toggleSort("score")}
              >
                <span className="inline-flex items-center gap-1">
                  Score
                  <SortIcon field="score" />
                </span>
              </th>
              <th className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4">
                Model
              </th>
              <th className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4">
                Duration
              </th>
              <th
                className="text-left text-xs font-medium text-stone-500 uppercase tracking-wider py-3 px-4 cursor-pointer select-none"
                onClick={() => toggleSort("time")}
              >
                <span className="inline-flex items-center gap-1">
                  Time
                  <SortIcon field="time" />
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((run) => (
              <HistoryRow key={run.id} run={run} onClick={() => onSelectRun(run)} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-stone-100">
        <span className="text-xs text-stone-500">
          Showing {showingFrom}-{showingTo} of {sorted.length} runs
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1.5 rounded-md text-xs font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 rounded-md text-xs font-medium border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
