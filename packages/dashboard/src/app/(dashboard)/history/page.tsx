"use client";

import { useState, useMemo, useCallback } from "react";
import { Download, ChevronDown } from "lucide-react";
import { useHistory } from "@/lib/hooks";
import { historyRuns as mockRuns, HistoryRun } from "@/lib/data/history";
import { HistoryFilters } from "@/components/history/history-filters";
import { HistoryTable } from "@/components/history/history-table";
import { RunDetailSheet } from "@/components/history/run-detail-sheet";
import { api, type HistorySearchResult } from "@/lib/api";

const EXPORT_FORMATS = [
  { id: "json", label: "JSON", ext: ".json" },
  { id: "csv", label: "CSV", ext: ".csv" },
  { id: "markdown", label: "Markdown", ext: ".md" },
  { id: "xliff", label: "XLIFF", ext: ".xliff" },
];

export default function HistoryPage() {
  const [agentFilter, setAgentFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedRun, setSelectedRun] = useState<HistoryRun | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [searchResults, setSearchResults] = useState<HistorySearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);

  const { data: apiHistory, loading } = useHistory({
    agent: agentFilter !== "all" ? agentFilter : undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const isLive = !!(apiHistory?.runs && apiHistory.runs.length > 0);

  const uniqueAgents = useMemo(() => {
    if (isLive && apiHistory?.runs) {
      const names = new Set(apiHistory.runs.map((r) => r.agent_slug));
      return Array.from(names).sort();
    }
    const names = new Set(mockRuns.map((r) => r.agent));
    return Array.from(names).sort();
  }, [apiHistory, isLive]);

  const runs = useMemo(() => {
    if (apiHistory?.runs && apiHistory.runs.length > 0) {
      return apiHistory.runs.map((r) => ({
        id: r.agent_slug + r.timestamp,
        agent: r.agent_slug,
        agentSlug: r.agent_slug,
        input: "",
        output: "",
        status: r.passed ? ("passed" as const) : ("failed" as const),
        score: r.composite_score,
        model: "",
        duration: "",
        time: r.timestamp,
        iterations: r.iteration_count,
        evaluation: {
          readability: r.scores?.readability ?? 0,
          linter: r.scores?.linter ?? 0,
          accessibility: r.scores?.accessibility ?? 0,
          voice: r.scores?.voice ?? 0,
        },
      }));
    }

    let filtered = mockRuns;
    if (agentFilter !== "all")
      filtered = filtered.filter((r) => r.agent === agentFilter);
    if (statusFilter !== "all")
      filtered = filtered.filter((r) => r.status === statusFilter);
    if (searchFilter)
      filtered = filtered.filter(
        (r) =>
          r.input.toLowerCase().includes(searchFilter.toLowerCase()) ||
          r.output.toLowerCase().includes(searchFilter.toLowerCase())
      );
    return filtered;
  }, [apiHistory, agentFilter, statusFilter, searchFilter]);

  const handleSearch = useCallback(async (query: string) => {
    setSearchFilter(query);
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const results = await api.searchHistory(query);
      setSearchResults(results);
    } catch {
      setSearchResults(null);
    } finally {
      setSearching(false);
    }
  }, []);

  const handleExport = useCallback(async (format: string) => {
    setExporting(true);
    setExportOpen(false);
    try {
      const entries = runs.map((r) => ({
        source: r.input || r.agent,
        target: r.output || `Score: ${r.score}`,
        agent: r.agent,
        context: r.time,
      }));
      const content = await api.exportContent(entries, format);
      const fmt = EXPORT_FORMATS.find((f) => f.id === format);
      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `history-export${fmt?.ext || ".txt"}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setExporting(false);
    }
  }, [runs]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-2xl font-semibold text-stone-900">History</h1>
            <span className="flex items-center gap-1 text-xs text-stone-400">
              <span
                className={`inline-block h-1.5 w-1.5 rounded-full ${
                  isLive ? "bg-emerald-500" : "bg-amber-400"
                }`}
              />
              {isLive ? "Live" : "Demo data"}
            </span>
          </div>
          <p className="text-stone-500 mt-1">Browse all past agent runs and evaluation results.</p>
        </div>

        {/* Export dropdown */}
        <div className="relative">
          <button
            onClick={() => setExportOpen(!exportOpen)}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border border-stone-200 text-stone-700 hover:bg-stone-50 transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {exporting ? "Exporting..." : "Export"}
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
          {exportOpen && (
            <div className="absolute right-0 mt-1 w-40 bg-white border border-stone-200 rounded-lg shadow-lg z-10 py-1">
              {EXPORT_FORMATS.map((fmt) => (
                <button
                  key={fmt.id}
                  onClick={() => handleExport(fmt.id)}
                  className="block w-full text-left px-4 py-2 text-sm text-stone-700 hover:bg-stone-50"
                >
                  {fmt.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div className="text-sm text-stone-400 animate-pulse">Loading history...</div>
      )}

      {/* Filters */}
      <HistoryFilters
        agents={uniqueAgents}
        agentFilter={agentFilter}
        statusFilter={statusFilter}
        searchFilter={searchFilter}
        onAgentChange={setAgentFilter}
        onStatusChange={setStatusFilter}
        onSearchChange={handleSearch}
      />

      {/* Content search results */}
      {searching && (
        <div className="text-sm text-stone-400 animate-pulse">Searching content versions...</div>
      )}
      {searchResults && searchResults.length > 0 && (
        <div className="bg-surface-card rounded-xl p-4 shadow-soft">
          <h3 className="text-sm font-semibold text-stone-700 mb-3">Content Version Matches</h3>
          <div className="space-y-3">
            {searchResults.slice(0, 10).map((r) => (
              <div key={r.id} className="border border-stone-100 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-brand-600">{r.agent_name}</span>
                  <span className="text-xs text-stone-400">{r.model}</span>
                </div>
                <p className="text-sm text-stone-600 line-clamp-1"><span className="font-medium">In:</span> {r.input_text}</p>
                <p className="text-sm text-stone-800 line-clamp-2 mt-1"><span className="font-medium">Out:</span> {r.output_text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {searchResults && searchResults.length === 0 && (
        <p className="text-sm text-stone-400">No content versions matched your search.</p>
      )}

      {/* Table */}
      <HistoryTable runs={runs} onSelectRun={setSelectedRun} />

      {/* Detail sheet */}
      <RunDetailSheet run={selectedRun} onClose={() => setSelectedRun(null)} />
    </div>
  );
}
