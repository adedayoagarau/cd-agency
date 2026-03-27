"use client";

import { useState, useMemo } from "react";
import { useAgents } from "@/lib/hooks";
import { agents as mockAgents, AgentCategory, categoryLabels, categoryColors } from "@/lib/data/agents";
import { AgentFilters } from "@/components/agents/agent-filters";
import { AgentGrid } from "@/components/agents/agent-grid";

export default function AgentsPage() {
  const [category, setCategory] = useState<AgentCategory | "all">("all");
  const [search, setSearch] = useState("");

  const { data: apiAgents, loading, error } = useAgents();

  const agentList = useMemo(() => {
    if (apiAgents && apiAgents.length > 0) {
      return apiAgents.map((a) => ({
        slug: a.slug,
        name: a.name,
        description: a.description,
        category: (a.tags?.[0] as AgentCategory) || "writing",
        model: a.model,
        tools: a.tools || [],
        qualityThreshold: a.threshold || 0.75,
        avgScore: 0,
        totalRuns: 0,
        lastUsed: null,
      }));
    }
    return mockAgents;
  }, [apiAgents]);

  const isLive = !!(apiAgents && apiAgents.length > 0);

  const filteredAgents = useMemo(() => {
    return agentList.filter((agent) => {
      const matchesCategory = category === "all" || agent.category === category;
      const query = search.toLowerCase();
      const matchesSearch =
        !query ||
        agent.name.toLowerCase().includes(query) ||
        agent.description.toLowerCase().includes(query);
      return matchesCategory && matchesSearch;
    });
  }, [category, search, agentList]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <p className="text-stone-500 text-sm">Loading agents...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <h1 className="font-serif text-2xl font-semibold text-stone-900">Agents</h1>
          {isLive ? (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-full px-2 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Live
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-100 rounded-full px-2 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
              Demo data
            </span>
          )}
        </div>
        <p className="text-stone-500 mt-1">
          Browse and run your content design agents.
        </p>
      </div>

      <div className="mb-6">
        <AgentFilters
          category={category}
          onCategoryChange={setCategory}
          search={search}
          onSearchChange={setSearch}
        />
      </div>

      <AgentGrid agents={filteredAgents} />
    </div>
  );
}
