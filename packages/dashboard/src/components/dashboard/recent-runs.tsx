import { ChevronRight } from "lucide-react";
import { RunItem } from "./run-item";

const runs = [
  {
    agent: "Microcopy Writer",
    input: '"Write a button label for a file upload action that feels encouraging but..."',
    status: "passed" as const,
    score: "92% Match",
    time: "Just now",
  },
  {
    agent: "Brand Voice Evaluator",
    input: "Analyzing homepage hero section against Q3 brand guidelines...",
    status: "iterating" as const,
    iteration: "2/3",
    time: "2m ago",
  },
  {
    agent: "Error Message Crafter",
    input: '"Payment failed due to expired credit card, need to prompt update"',
    status: "passed" as const,
    score: "88% Match",
    time: "1h ago",
  },
  {
    agent: "SEO Meta Generator",
    input: '"Generate meta tags for the new Enterprise pricing page focusing on..."',
    status: "failed" as const,
    time: "3h ago",
  },
  {
    agent: "Tone Adjuster (Formal)",
    input: '"Hey folks, we\'re super pumped to announce our new feature drop..."',
    status: "passed" as const,
    score: "95% Match",
    time: "Yesterday",
  },
];

export function RecentRuns({ className }: { className?: string }) {
  return (
    <div className={`bg-surface-card rounded-xl p-6 shadow-soft ${className ?? ""}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-stone-900">Recent Runs</h3>
        <a
          href="#"
          className="inline-flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700 transition-colors"
        >
          View all history
          <ChevronRight className="w-4 h-4" />
        </a>
      </div>

      {/* Runs list */}
      <div>
        {runs.map((run, i) => (
          <RunItem key={i} {...run} isFirst={i === 0} />
        ))}
      </div>
    </div>
  );
}
