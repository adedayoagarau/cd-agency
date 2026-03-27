"use client";

import { Search } from "lucide-react";
import { AgentCategory, categoryLabels } from "@/lib/data/agents";

interface AgentFiltersProps {
  category: AgentCategory | "all";
  onCategoryChange: (category: AgentCategory | "all") => void;
  search: string;
  onSearchChange: (search: string) => void;
}

const filterOptions: { value: AgentCategory | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "writing", label: categoryLabels.writing },
  { value: "evaluation", label: categoryLabels.evaluation },
  { value: "optimization", label: categoryLabels.optimization },
  { value: "translation", label: categoryLabels.translation },
];

export function AgentFilters({
  category,
  onCategoryChange,
  search,
  onSearchChange,
}: AgentFiltersProps) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex items-center gap-1">
        {filterOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onCategoryChange(option.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              category === option.value
                ? "bg-brand-50 text-brand-700 border-brand-200"
                : "bg-white text-stone-600 border-stone-200 hover:bg-stone-50"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
        <input
          type="text"
          placeholder="Search agents..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-64 pl-9 pr-4 py-2 rounded-lg border border-stone-200 bg-white text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
        />
      </div>
    </div>
  );
}
