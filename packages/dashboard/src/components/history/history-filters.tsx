"use client";

import { Search } from "lucide-react";

interface HistoryFiltersProps {
  agents: string[];
  agentFilter: string;
  statusFilter: string;
  searchFilter: string;
  onAgentChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSearchChange: (value: string) => void;
}

const statusOptions = [
  { label: "All", value: "all" },
  { label: "Passed", value: "passed" },
  { label: "Failed", value: "failed" },
];

export function HistoryFilters({
  agents,
  agentFilter,
  statusFilter,
  searchFilter,
  onAgentChange,
  onStatusChange,
  onSearchChange,
}: HistoryFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Agent dropdown */}
      <select
        value={agentFilter}
        onChange={(e) => onAgentChange(e.target.value)}
        className="bg-white border border-stone-200 rounded-lg px-3 py-2 text-sm text-stone-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
      >
        <option value="all">All agents</option>
        {agents.map((agent) => (
          <option key={agent} value={agent}>
            {agent}
          </option>
        ))}
      </select>

      {/* Status pills */}
      <div className="flex items-center gap-2">
        {statusOptions.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onStatusChange(opt.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              statusFilter === opt.value
                ? "bg-brand-50 text-brand-700 border-brand-200"
                : "bg-white text-stone-500 border-stone-200 hover:bg-stone-50"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
        <input
          type="text"
          placeholder="Search content..."
          value={searchFilter}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-48 bg-white border border-stone-200 rounded-lg pl-9 pr-3 py-2 text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
        />
      </div>
    </div>
  );
}
