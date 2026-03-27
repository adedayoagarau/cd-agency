"use client";

import { useState, useMemo } from "react";
import { useMemorySearch, useMemoryStats } from "@/lib/hooks";
import { memoryEntries as mockEntries, MemoryScope } from "@/lib/data/memory";
import { MemorySearch } from "@/components/memory/memory-search";
import { MemoryCard } from "@/components/memory/memory-card";
import { MemoryStats } from "@/components/memory/memory-stats";

export default function MemoryPage() {
  const [search, setSearch] = useState("");
  const [scope, setScope] = useState<MemoryScope | "all">("all");

  const { data: searchResults, loading: searchLoading } = useMemorySearch(
    search,
    scope === "all" ? undefined : scope
  );
  const { data: stats } = useMemoryStats();

  const isLive = !!(searchResults && search) || !!stats;

  const filteredEntries = useMemo(() => {
    // If we have API search results and an active search query, use them
    if (searchResults && searchResults.length > 0 && search) {
      return searchResults.map((r) => ({
        id: r.key,
        scope: r.scope,
        content: r.value,
        source: r.source_agent,
        tags: [r.category],
        createdAt: r.timestamp,
        relevance: r.relevance_score,
      }));
    }

    // Fall back to mock data with local filtering
    return mockEntries.filter((entry) => {
      const matchesScope = scope === "all" || entry.scope === scope;
      const query = search.toLowerCase();
      const matchesSearch =
        !query ||
        entry.content.toLowerCase().includes(query) ||
        entry.source.toLowerCase().includes(query) ||
        entry.tags.some((tag) => tag.toLowerCase().includes(query));
      return matchesScope && matchesSearch;
    });
  }, [search, scope, searchResults]);

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <h1 className="font-serif text-2xl font-semibold text-stone-900">
            Memory
          </h1>
          <span className="flex items-center gap-1 text-xs text-stone-400">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${
                isLive ? "bg-emerald-500" : "bg-amber-400"
              }`}
            />
            {isLive ? "Live" : "Demo data"}
          </span>
        </div>
        <p className="text-stone-500 mt-1">
          Search across your content workspace memory.
        </p>
      </div>

      {/* Search and filters */}
      <MemorySearch
        search={search}
        onSearchChange={setSearch}
        scope={scope}
        onScopeChange={setScope}
      />

      {/* Loading indicator */}
      {searchLoading && search && (
        <div className="mt-4 text-sm text-stone-400 animate-pulse">
          Searching memory...
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-6">
        {/* Left: memory cards */}
        <div className="lg:col-span-3 space-y-3">
          {filteredEntries.map((entry) => (
            <MemoryCard key={entry.id} entry={entry} />
          ))}
          {filteredEntries.length === 0 && !searchLoading && (
            <div className="bg-surface-card rounded-xl p-8 text-center border border-stone-100">
              <p className="text-sm text-stone-400">
                No memory entries match your search.
              </p>
            </div>
          )}
        </div>

        {/* Right: stats sidebar */}
        <div className="lg:col-span-1">
          <MemoryStats stats={stats ?? undefined} />
        </div>
      </div>
    </div>
  );
}
