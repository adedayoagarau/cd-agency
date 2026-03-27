"use client";

import { useState } from "react";
import { Search, Plus, Save } from "lucide-react";
import { terminology as mockTerminology } from "@/lib/data/brand-dna";

type TerminologyEntry = { term: string; preferred: string; avoid: string; severity: "required" | "preferred" };

interface TerminologyTabProps {
  data?: TerminologyEntry[];
  onSave?: (terminology: TerminologyEntry[]) => void;
}

export function TerminologyTab({ data, onSave }: TerminologyTabProps) {
  const [search, setSearch] = useState("");
  const terms = data ?? mockTerminology;

  const filtered = terms.filter((item) => {
    const q = search.toLowerCase();
    if (!q) return true;
    return (
      item.term.toLowerCase().includes(q) ||
      item.preferred.toLowerCase().includes(q) ||
      item.avoid.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      {/* Search bar */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
        <input
          type="text"
          placeholder="Search terminology..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full h-10 pl-10 pr-4 rounded-lg border border-stone-200 bg-white text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-200 focus:border-brand-300 transition-colors"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-stone-100 overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_1.2fr_1.5fr_0.7fr] gap-4 px-5 py-3 border-b border-stone-100 text-xs font-semibold text-stone-500 uppercase tracking-wider">
          <span>Term</span>
          <span>Preferred usage</span>
          <span>Avoid</span>
          <span>Severity</span>
        </div>

        {/* Rows */}
        {filtered.map((item) => (
          <div
            key={item.term}
            className="grid grid-cols-[1fr_1.2fr_1.5fr_0.7fr] gap-4 px-5 py-3.5 border-b border-stone-50 last:border-b-0 hover:bg-stone-50 transition-colors"
          >
            <span className="text-sm font-medium text-stone-800">
              {item.term}
            </span>
            <span className="text-sm text-stone-600">{item.preferred}</span>
            <span className="text-sm text-stone-500">{item.avoid}</span>
            <div>
              {item.severity === "required" ? (
                <span className="bg-rose-50 text-rose-700 border border-rose-100 rounded-full px-2 py-0.5 text-[10px] uppercase font-bold">
                  Required
                </span>
              ) : (
                <span className="bg-amber-50 text-amber-700 border border-amber-100 rounded-full px-2 py-0.5 text-[10px] uppercase font-bold">
                  Preferred
                </span>
              )}
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="px-5 py-8 text-center text-sm text-stone-400">
            No terms match your search.
          </div>
        )}
      </div>

      {/* Add term button */}
      <button
        type="button"
        className="mt-4 text-sm text-brand-600 border border-dashed border-brand-200 rounded-lg p-2 w-full flex items-center justify-center gap-1.5 hover:bg-brand-50 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add term
      </button>

      {onSave && (
        <button
          type="button"
          onClick={() => onSave(terms)}
          className="mt-4 bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:bg-brand-600 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save
        </button>
      )}
    </div>
  );
}
