"use client";

import { useState } from "react";

interface SliderRowProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

function SliderRow({ label, value, onChange, min = 0, max = 1, step = 0.05 }: SliderRowProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-stone-700">{label}</span>
        <span className="text-sm font-semibold text-stone-900">{value.toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer bg-stone-200 accent-brand-500"
        style={{ accentColor: "#C65D3B" }}
      />
    </div>
  );
}

interface QualityThresholdsProps {
  initialData?: Record<string, number> | null;
  onSave?: (thresholds: Record<string, number>) => Promise<void>;
}

export function QualityThresholds({ initialData, onSave }: QualityThresholdsProps) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [readability, setReadability] = useState(initialData?.readability ?? 0.75);
  const [linter, setLinter] = useState(initialData?.linter ?? 0.80);
  const [accessibility, setAccessibility] = useState(initialData?.accessibility ?? 0.70);
  const [voice, setVoice] = useState(initialData?.voice ?? 0.75);
  const [composite, setComposite] = useState(initialData?.composite ?? 0.75);
  const [maxIterations, setMaxIterations] = useState(initialData?.max_iterations ?? 3);

  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft">
      <h3 className="text-base font-semibold text-stone-900">
        Default Quality Thresholds
      </h3>
      <p className="text-sm text-stone-500 mb-6">
        Global defaults for agent evaluations. Individual agents can override.
      </p>

      <div className="space-y-5">
        <SliderRow label="Readability" value={readability} onChange={setReadability} />
        <SliderRow label="Linter" value={linter} onChange={setLinter} />
        <SliderRow label="Accessibility" value={accessibility} onChange={setAccessibility} />
        <SliderRow label="Voice Consistency" value={voice} onChange={setVoice} />

        {/* Composite threshold - slightly more prominent */}
        <div className="pt-2 border-t border-stone-100">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-stone-800">Composite Threshold</span>
              <span className="text-base font-bold text-stone-900">{composite.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={composite}
              onChange={(e) => setComposite(parseFloat(e.target.value))}
              className="w-full h-2.5 rounded-full appearance-none cursor-pointer bg-stone-200"
              style={{ accentColor: "#C65D3B" }}
            />
          </div>
        </div>

        {/* Max iterations */}
        <div className="flex items-center justify-between pt-2 border-t border-stone-100">
          <span className="text-sm font-medium text-stone-700">Max iterations</span>
          <input
            type="number"
            min={1}
            max={5}
            value={maxIterations}
            onChange={(e) => setMaxIterations(parseInt(e.target.value, 10))}
            className="w-20 border border-stone-200 rounded-lg px-3 py-1.5 text-sm text-stone-800 text-center focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          />
        </div>
        {onSave && (
          <div className="pt-4 border-t border-stone-100">
            <button
              type="button"
              disabled={saving}
              onClick={async () => {
                setSaving(true);
                setSaved(false);
                try {
                  await onSave({
                    readability,
                    linter,
                    accessibility,
                    voice,
                    composite,
                    max_iterations: maxIterations,
                  });
                  setSaved(true);
                  setTimeout(() => setSaved(false), 2000);
                } finally {
                  setSaving(false);
                }
              }}
              className="bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-50"
            >
              {saving ? "Saving..." : saved ? "Saved" : "Save Thresholds"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
