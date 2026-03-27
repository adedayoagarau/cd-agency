"use client";

import { Search } from "lucide-react";
import { MemoryScope } from "@/lib/data/memory";

const scopeFilters = [
  { id: "all" as const, label: "All" },
  { id: "session" as const, label: "Session" },
  { id: "project" as const, label: "Project" },
  { id: "workspace" as const, label: "Workspace" },
];

interface MemorySearchProps {
  search: string;
  onSearchChange: (value: string) => void;
  scope: MemoryScope | "all";
  onScopeChange: (scope: MemoryScope | "all") => void;
}

export function MemorySearch({
  search,
  onSearchChange,
  scope,
  onScopeChange,
}: MemorySearchProps) {
  return (
    <div>
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400" />
        <input
          type="text"
          placeholder="Search memory entries..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full h-12 pl-12 pr-4 rounded-xl bg-white border border-stone-200 text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-200 focus:border-brand-300 transition-colors"
        />
      </div>

      {/* Scope filter pills */}
      <div className="flex items-center gap-2 mt-3">
        {scopeFilters.map((filter) => (
          <button
            key={filter.id}
            type="button"
            onClick={() => onScopeChange(filter.id)}
            className={`text-xs font-medium rounded-full px-3 py-1.5 border transition-colors ${
              scope === filter.id
                ? "bg-brand-50 text-brand-700 border-brand-200"
                : "bg-white text-stone-500 border-stone-200 hover:text-stone-700"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>
    </div>
  );
}
