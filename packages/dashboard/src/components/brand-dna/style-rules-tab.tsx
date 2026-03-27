"use client";

import { Plus, Save } from "lucide-react";
import { styleRules as mockStyleRules } from "@/lib/data/brand-dna";

type StyleRule = { rule: string; severity: "required" | "preferred"; category: string };

interface StyleRulesTabProps {
  data?: StyleRule[];
  onSave?: (rules: StyleRule[]) => void;
}

const categoryColors: Record<string, string> = {
  Capitalization: "bg-blue-50 text-blue-700",
  Punctuation: "bg-purple-50 text-purple-700",
  Numbers: "bg-emerald-50 text-emerald-700",
  Readability: "bg-amber-50 text-amber-700",
  Messaging: "bg-brand-50 text-brand-700",
  Tone: "bg-stone-100 text-stone-700",
};

export function StyleRulesTab({ data, onSave }: StyleRulesTabProps) {
  const rules = data ?? mockStyleRules;

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {rules.map((rule) => (
          <div
            key={rule.rule}
            className="bg-white rounded-lg p-4 border border-stone-100"
          >
            {/* Top row: category + severity */}
            <div className="flex items-center justify-between">
              <span
                className={`text-[10px] uppercase font-bold rounded-full px-2 py-0.5 ${categoryColors[rule.category] || "bg-stone-100 text-stone-700"}`}
              >
                {rule.category}
              </span>
              {rule.severity === "required" ? (
                <span className="bg-rose-50 text-rose-700 border border-rose-100 rounded-full px-2 py-0.5 text-[10px] uppercase font-bold">
                  Required
                </span>
              ) : (
                <span className="bg-amber-50 text-amber-700 border border-amber-100 rounded-full px-2 py-0.5 text-[10px] uppercase font-bold">
                  Preferred
                </span>
              )}
            </div>

            {/* Rule text */}
            <p className="text-sm text-stone-700 mt-2">{rule.rule}</p>
          </div>
        ))}
      </div>

      {/* Add rule button */}
      <button
        type="button"
        className="mt-4 text-sm text-brand-600 border border-dashed border-brand-200 rounded-lg p-2 w-full flex items-center justify-center gap-1.5 hover:bg-brand-50 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add rule
      </button>

      {onSave && (
        <button
          type="button"
          onClick={() => onSave(rules)}
          className="mt-4 bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:bg-brand-600 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save
        </button>
      )}
    </div>
  );
}
