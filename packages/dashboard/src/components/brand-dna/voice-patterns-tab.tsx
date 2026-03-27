"use client";

import { Plus, Save } from "lucide-react";
import { voicePatterns as mockVoicePatterns } from "@/lib/data/brand-dna";

type VoicePattern = { dimension: string; value: string; confidence: number; source: string };

interface VoicePatternsTabProps {
  data?: VoicePattern[];
  onSave?: (patterns: VoicePattern[]) => void;
}

export function VoicePatternsTab({ data, onSave }: VoicePatternsTabProps) {
  const patterns = data ?? mockVoicePatterns;

  return (
    <div>
      <div className="bg-white rounded-xl border border-stone-100 overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[1.2fr_1.5fr_0.8fr_1fr] gap-4 px-5 py-3 border-b border-stone-100 text-xs font-semibold text-stone-500 uppercase tracking-wider">
          <span>Dimension</span>
          <span>Pattern</span>
          <span>Confidence</span>
          <span>Source</span>
        </div>

        {/* Rows */}
        {patterns.map((pattern) => (
          <div
            key={pattern.dimension}
            className="grid grid-cols-[1.2fr_1.5fr_0.8fr_1fr] gap-4 px-5 py-3.5 border-b border-stone-50 last:border-b-0 hover:bg-stone-50 transition-colors"
          >
            <span className="text-sm font-medium text-stone-800">
              {pattern.dimension}
            </span>
            <span className="text-sm text-stone-600">{pattern.value}</span>
            <div className="flex items-center gap-2">
              <div className="w-full h-1.5 rounded-full bg-stone-100">
                <div
                  className="h-1.5 rounded-full bg-brand-500 transition-all"
                  style={{ width: `${pattern.confidence * 100}%` }}
                />
              </div>
              <span className="text-xs text-stone-400 whitespace-nowrap">
                {Math.round(pattern.confidence * 100)}%
              </span>
            </div>
            <span className="text-xs text-stone-400">{pattern.source}</span>
          </div>
        ))}
      </div>

      {/* Add new pattern button */}
      <button
        type="button"
        className="mt-4 text-sm text-brand-600 border border-dashed border-brand-200 rounded-lg p-2 w-full flex items-center justify-center gap-1.5 hover:bg-brand-50 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add new pattern
      </button>

      {onSave && (
        <button
          type="button"
          onClick={() => onSave(patterns)}
          className="mt-4 bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:bg-brand-600 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save
        </button>
      )}
    </div>
  );
}
