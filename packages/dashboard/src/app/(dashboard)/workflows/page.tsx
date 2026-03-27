"use client";

import { GitBranch, ArrowRight, Loader2 } from "lucide-react";
import Link from "next/link";
import { useWorkflows } from "@/lib/hooks";

const mockWorkflows = [
  { slug: "content-audit", name: "Content Audit", description: "Full content quality audit across readability, linting, and accessibility.", step_count: 4 },
  { slug: "ux-copy-pipeline", name: "UX Copy Pipeline", description: "Generate, review, and polish UX microcopy end-to-end.", step_count: 3 },
  { slug: "brand-alignment", name: "Brand Alignment Check", description: "Verify content aligns with brand voice, terminology, and style rules.", step_count: 5 },
  { slug: "localization-prep", name: "Localization Prep", description: "Prepare content for localization: simplify, check idioms, extract strings.", step_count: 4 },
  { slug: "error-message-suite", name: "Error Message Suite", description: "Generate a complete set of error messages for a feature.", step_count: 3 },
  { slug: "onboarding-flow", name: "Onboarding Flow Writer", description: "Design and write all copy for an onboarding flow.", step_count: 6 },
];

export default function WorkflowsPage() {
  const { data: apiWorkflows, loading } = useWorkflows();
  const workflows = apiWorkflows && apiWorkflows.length > 0 ? apiWorkflows : mockWorkflows;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">Workflows</h1>
        <p className="text-stone-500 mt-1">Multi-agent pipelines that chain agents together for complex content tasks.</p>
      </div>

      {loading && <div className="text-sm text-stone-400 animate-pulse">Loading workflows...</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.map((wf) => (
          <Link
            key={wf.slug}
            href={`/workflows/${wf.slug}`}
            className="bg-surface-card rounded-xl p-5 shadow-soft border border-transparent hover:border-brand-200 hover:shadow-md transition-all group"
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-brand-50 flex items-center justify-center">
                <GitBranch className="w-4 h-4 text-brand-600" />
              </div>
              <h3 className="text-sm font-semibold text-stone-900">{wf.name}</h3>
            </div>
            <p className="text-xs text-stone-500 mb-4 line-clamp-2">{wf.description}</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-stone-400">{wf.step_count} steps</span>
              <ArrowRight className="w-4 h-4 text-stone-300 group-hover:text-brand-500 transition-colors" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
