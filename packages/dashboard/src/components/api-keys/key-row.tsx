import { Check } from "lucide-react";

interface KeyRowProps {
  name: string;
  connected: boolean;
  maskedKey: string | null;
  lastUsed: string | null;
  onTest?: () => void;
  onEdit?: () => void;
  onRemove?: () => void;
  onAdd?: () => void;
}

export function KeyRow({
  name,
  connected,
  maskedKey,
  lastUsed,
  onTest,
  onEdit,
  onRemove,
  onAdd,
}: KeyRowProps) {
  return (
    <div className="flex items-center gap-4 p-4">
      {/* Name */}
      <span className="text-sm font-medium text-stone-800 min-w-[100px]">
        {name}
      </span>

      {/* Connection status */}
      <div className="flex items-center gap-3 flex-1">
        {connected ? (
          <>
            <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span className="font-mono text-xs text-stone-500 bg-stone-50 px-2 py-1 rounded">
              {maskedKey}
            </span>
            {lastUsed && (
              <span className="text-xs text-stone-400">
                Last used: {lastUsed}
              </span>
            )}
          </>
        ) : (
          <span className="text-sm text-stone-400">Not configured</span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {connected ? (
          <>
            <button
              onClick={onTest}
              className="text-xs px-3 py-1 rounded-md border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
            >
              Test
            </button>
            <button
              onClick={onEdit}
              className="text-xs px-3 py-1 rounded-md border border-stone-200 text-stone-600 hover:bg-stone-50 transition-colors"
            >
              Edit
            </button>
            <button
              onClick={onRemove}
              className="text-xs text-rose-500 hover:text-rose-700 hover:bg-rose-50 px-3 py-1 rounded-md transition-colors"
            >
              Remove
            </button>
          </>
        ) : (
          <button
            onClick={onAdd}
            className="bg-brand-500 text-white text-xs px-3 py-1.5 rounded-md hover:bg-brand-600 transition-colors"
          >
            Add Key
          </button>
        )}
      </div>
    </div>
  );
}
