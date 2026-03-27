"use client";

import { useState } from "react";
import { Palette, ChevronRight, X } from "lucide-react";
import { usePresets, usePreset } from "@/lib/hooks";

const mockPresets = [
  { name: "Material Design", filename: "material.yaml" },
  { name: "Shopify Polaris", filename: "polaris.yaml" },
  { name: "Atlassian Design", filename: "atlassian.yaml" },
  { name: "Apple HIG", filename: "apple-hig.yaml" },
];

const presetColors: Record<string, string> = {
  "Material Design": "bg-blue-50 border-blue-200 text-blue-700",
  "Shopify Polaris": "bg-green-50 border-green-200 text-green-700",
  "Atlassian Design": "bg-indigo-50 border-indigo-200 text-indigo-700",
  "Apple HIG": "bg-stone-50 border-stone-200 text-stone-700",
};

export default function PresetsPage() {
  const { data: apiPresets, loading } = usePresets();
  const presets = apiPresets && apiPresets.length > 0 ? apiPresets : mockPresets;
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">Design System Presets</h1>
        <p className="text-stone-500 mt-1">Apply voice and style rules from popular design systems to your content.</p>
      </div>

      {loading && <div className="text-sm text-stone-400 animate-pulse">Loading presets...</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {presets.map((preset) => (
          <button
            key={preset.name}
            onClick={() => setSelectedPreset(preset.name)}
            className={`text-left bg-surface-card rounded-xl p-5 shadow-soft border border-transparent hover:border-brand-200 hover:shadow-md transition-all`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${presetColors[preset.name] || "bg-brand-50 text-brand-700"}`}>
                  <Palette className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-semibold text-stone-900">{preset.name}</h3>
              </div>
              <ChevronRight className="w-4 h-4 text-stone-300" />
            </div>
            <p className="text-xs text-stone-500">
              Voice and style rules for the {preset.name} design system.
            </p>
          </button>
        ))}
      </div>

      {/* Detail sheet */}
      {selectedPreset && (
        <PresetDetailSheet name={selectedPreset} onClose={() => setSelectedPreset(null)} />
      )}
    </div>
  );
}

function PresetDetailSheet({ name, onClose }: { name: string; onClose: () => void }) {
  const { data: preset, loading } = usePreset(name);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/20" />
      <div
        className="relative w-full max-w-lg bg-white shadow-xl overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-serif text-xl font-semibold text-stone-900">{name}</h2>
            <button onClick={onClose} className="p-1 rounded-full hover:bg-stone-100">
              <X className="w-5 h-5 text-stone-400" />
            </button>
          </div>

          {loading ? (
            <div className="text-sm text-stone-400 animate-pulse">Loading preset...</div>
          ) : preset ? (
            <div className="space-y-6">
              {preset.tone_descriptors?.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-stone-700 mb-2">Tone</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {preset.tone_descriptors.map((t: string) => (
                      <span key={t} className="px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-medium">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {preset.do_rules?.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-stone-700 mb-2">Do</h3>
                  <ul className="space-y-1">
                    {preset.do_rules.map((rule: string, i: number) => (
                      <li key={i} className="text-xs text-stone-600 flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">&#10003;</span>
                        {rule}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {preset.dont_rules?.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-stone-700 mb-2">Don&apos;t</h3>
                  <ul className="space-y-1">
                    {preset.dont_rules.map((rule: string, i: number) => (
                      <li key={i} className="text-xs text-stone-600 flex items-start gap-2">
                        <span className="text-rose-500 mt-0.5">&#10007;</span>
                        {rule}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {preset.sample_content?.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-stone-700 mb-2">Examples</h3>
                  <div className="space-y-2">
                    {preset.sample_content.map((s: string, i: number) => (
                      <div key={i} className="text-xs text-stone-600 p-3 rounded bg-stone-50 border border-stone-100 italic">
                        &ldquo;{s}&rdquo;
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {preset.character_limits && Object.keys(preset.character_limits).length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-stone-700 mb-2">Character Limits</h3>
                  <div className="space-y-1">
                    {Object.entries(preset.character_limits).map(([element, limit]) => (
                      <div key={element} className="flex justify-between text-xs text-stone-600">
                        <span>{element}</span>
                        <span className="font-medium">{String(limit)} chars</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-stone-500">Preset not found.</p>
          )}
        </div>
      </div>
    </div>
  );
}
