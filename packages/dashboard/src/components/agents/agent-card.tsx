"use client";

import Link from "next/link";
import { Cpu, Wrench } from "lucide-react";
import { Agent, categoryLabels, categoryColors } from "@/lib/data/agents";

interface AgentCardProps {
  agent: Agent;
}

function getScoreColor(score: number): string {
  if (score >= 0.9) return "text-emerald-600";
  if (score >= 0.8) return "text-brand-600";
  return "text-amber-600";
}

export function AgentCard({ agent }: AgentCardProps) {
  const scorePercent = Math.round(agent.avgScore * 100);
  const scoreColor = getScoreColor(agent.avgScore);

  return (
    <Link href={`/agents/${agent.slug}`} className="block">
      <div className="bg-surface-card rounded-xl p-6 shadow-soft hover:shadow-md transition-shadow border border-transparent hover:border-brand-200 cursor-pointer h-full flex flex-col">
        {/* Top row: category badge + score */}
        <div className="flex items-center justify-between mb-3">
          <span
            className={`text-[10px] uppercase font-bold tracking-wider rounded-full px-2 py-0.5 border ${categoryColors[agent.category]}`}
          >
            {categoryLabels[agent.category]}
          </span>
          <span className={`text-lg font-semibold ${scoreColor}`}>
            {scorePercent}%
          </span>
        </div>

        {/* Agent name */}
        <h3 className="font-serif text-lg font-medium text-stone-800 mb-1">
          {agent.name}
        </h3>

        {/* Description */}
        <p className="text-sm text-stone-500 line-clamp-2 mb-3">
          {agent.description}
        </p>

        {/* Model + tools row */}
        <div className="flex items-center gap-4 text-xs text-stone-400">
          <span className="inline-flex items-center gap-1">
            <Cpu className="w-3 h-3" />
            {agent.model}
          </span>
          <span className="inline-flex items-center gap-1">
            <Wrench className="w-3 h-3" />
            {agent.tools.length} tools
          </span>
        </div>

        {/* Separator */}
        <div className="border-t border-stone-100 my-4" />

        {/* Footer */}
        <div className="flex items-center justify-between mt-auto">
          <span className="text-xs text-stone-400">
            {agent.totalRuns} runs{agent.lastUsed ? ` · Last used ${agent.lastUsed}` : ""}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              className="text-stone-600 border border-stone-200 text-sm px-4 py-1.5 rounded-md hover:bg-stone-50 transition-colors"
            >
              Configure
            </button>
            <span className="bg-brand-500 text-white text-sm px-4 py-1.5 rounded-md hover:bg-brand-600 transition-colors">
              Run
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
