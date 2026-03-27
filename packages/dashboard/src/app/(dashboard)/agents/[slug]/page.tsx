"use client";

import { use, useMemo } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronRight, Cpu } from "lucide-react";
import { useAgent, useRunAgent, useStreamAgentRun } from "@/lib/hooks";
import { agents as mockAgents, categoryLabels, categoryColors, AgentCategory } from "@/lib/data/agents";
import { AgentRunInput } from "@/components/agents/agent-run-input";
import { AgentRunOutput } from "@/components/agents/agent-run-output";

interface AgentDetailPageProps {
  params: Promise<{ slug: string }>;
}

export default function AgentDetailPage({ params }: AgentDetailPageProps) {
  const { slug } = use(params);
  const { data: apiAgent, loading: agentLoading } = useAgent(slug);
  const { run: httpRun, result: httpResult, loading: httpLoading, error: httpError } = useRunAgent();
  const { stream, chunks, evaluation, status: streamStatus } = useStreamAgentRun();

  const agent = useMemo(() => {
    if (apiAgent) {
      return {
        slug: apiAgent.slug,
        name: apiAgent.name,
        description: apiAgent.description,
        category: (apiAgent.tags?.[0] as AgentCategory) || "writing",
        model: apiAgent.model,
        tools: apiAgent.tools || [],
        qualityThreshold: apiAgent.threshold || 0.75,
        avgScore: 0,
        totalRuns: 0,
        lastUsed: null,
      };
    }
    return mockAgents.find((a) => a.slug === slug) ?? null;
  }, [apiAgent, slug]);

  if (agentLoading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <p className="text-stone-500 text-sm">Loading agent...</p>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <h1 className="font-serif text-2xl font-semibold text-stone-900 mb-2">
          Agent not found
        </h1>
        <p className="text-stone-500 mb-4">
          No agent matches the slug &ldquo;{slug}&rdquo;.
        </p>
        <Link
          href="/agents"
          className="inline-flex items-center gap-1.5 text-brand-600 hover:text-brand-700 text-sm font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Agents
        </Link>
      </div>
    );
  }

  const isStreaming = streamStatus === "running";
  const displayLoading = isStreaming || httpLoading;

  const handleRun = async (input: string) => {
    try {
      stream({ agent_slug: agent.slug, content: input });
    } catch {
      // Fallback to HTTP
      await httpRun({ agent_slug: agent.slug, content: input });
    }
  };

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1 text-sm text-stone-400 mb-6">
        <Link href="/agents" className="hover:text-stone-600 transition-colors">
          Agents
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-stone-600">{agent.name}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="font-serif text-2xl font-semibold text-stone-900">
              {agent.name}
            </h1>
            <span
              className={`text-[10px] uppercase font-bold tracking-wider rounded-full px-2 py-0.5 border ${categoryColors[agent.category]}`}
            >
              {categoryLabels[agent.category]}
            </span>
            <span className="inline-flex items-center gap-1 text-xs text-stone-400 bg-stone-100 rounded-full px-2 py-0.5">
              <Cpu className="w-3 h-3" />
              {agent.model}
            </span>
          </div>
          <p className="text-stone-500">{agent.description}</p>
        </div>
        <Link
          href="/agents"
          className="inline-flex items-center gap-1.5 text-stone-600 hover:text-stone-800 text-sm font-medium transition-colors shrink-0"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Agents
        </Link>
      </div>

      {/* Run error */}
      {httpError && (
        <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {httpError}
        </div>
      )}
      {streamStatus === "error" && (
        <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          Streaming connection failed. Please try again.
        </div>
      )}

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentRunInput agent={agent} onRun={handleRun} loading={displayLoading} />
        <AgentRunOutput
          result={httpResult}
          loading={displayLoading}
          streamingContent={chunks}
          streamingEvaluation={evaluation}
          streamingStatus={streamStatus}
        />
      </div>
    </div>
  );
}
