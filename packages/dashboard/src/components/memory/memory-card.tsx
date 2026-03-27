import { MemoryEntry, scopeColors } from "@/lib/data/memory";

interface MemoryCardProps {
  entry: MemoryEntry;
}

export function MemoryCard({ entry }: MemoryCardProps) {
  return (
    <div className="bg-surface-card rounded-xl p-5 shadow-sm border border-stone-100">
      {/* Top row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] uppercase font-bold rounded-full px-2 py-0.5 border ${scopeColors[entry.scope]}`}
          >
            {entry.scope}
          </span>
          <span className="text-xs text-stone-400">{entry.createdAt}</span>
        </div>
        {entry.relevance !== undefined && (
          <span className="text-xs font-medium text-brand-600">
            {Math.round(entry.relevance * 100)}% match
          </span>
        )}
      </div>

      {/* Content */}
      <p className="text-sm text-stone-700 leading-relaxed line-clamp-3">
        {entry.content}
      </p>

      {/* Bottom row */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-stone-50">
        <span className="text-xs text-stone-400">Source: {entry.source}</span>
        <div className="flex items-center gap-1.5">
          {entry.tags.map((tag) => (
            <span
              key={tag}
              className="bg-stone-100 text-stone-500 rounded-full px-2 py-0.5 text-[10px]"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
