"use client";

import { useState } from "react";

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-11 h-6 rounded-full transition-colors ${
        enabled ? "bg-brand-500" : "bg-stone-200"
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
          enabled ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  );
}

interface CouncilStatusData {
  enabled: boolean;
  min_models: number;
  consensus_method: string;
  trigger_conditions: string[];
}

interface CouncilConfigProps {
  initialData?: CouncilStatusData | null;
  onSave?: (config: CouncilStatusData) => Promise<void>;
}

export function CouncilConfig({ initialData, onSave }: CouncilConfigProps) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const triggerConditions = initialData?.trigger_conditions ?? [];
  const [enabled, setEnabled] = useState(initialData?.enabled ?? true);
  const [minModels, setMinModels] = useState(initialData?.min_models ?? 2);
  const [consensus, setConsensus] = useState(initialData?.consensus_method ?? "weighted-median");
  const [conditions, setConditions] = useState({
    always: triggerConditions.includes("always") || (!initialData && true),
    manualOnly: triggerConditions.includes("manual_only") || false,
    highStakes: triggerConditions.includes("high_stakes") || false,
    lowConfidence: triggerConditions.includes("low_confidence") || (!initialData && true),
    failedThreshold: triggerConditions.includes("failed_threshold") || (!initialData && true),
  });

  function toggleCondition(key: keyof typeof conditions) {
    setConditions((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft">
      <h3 className="text-base font-semibold text-stone-900 mb-4">
        Council Configuration
      </h3>

      {/* Main toggle */}
      <div className="flex items-center justify-between mb-5">
        <span className="text-sm font-medium text-stone-700">
          Multi-model quality gate
        </span>
        <Toggle enabled={enabled} onChange={setEnabled} />
      </div>

      {enabled && (
        <div className="space-y-5 pt-4 border-t border-stone-100">
          {/* Min models */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-stone-700">
              Min models
            </label>
            <input
              type="number"
              min={2}
              max={4}
              value={minModels}
              onChange={(e) => setMinModels(parseInt(e.target.value, 10))}
              className="w-20 border border-stone-200 rounded-lg px-3 py-1.5 text-sm text-stone-800 text-center focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
          </div>

          {/* Consensus method */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-stone-700">
              Consensus method
            </label>
            <select
              value={consensus}
              onChange={(e) => setConsensus(e.target.value)}
              className="border border-stone-200 rounded-lg px-3 py-1.5 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 bg-white"
            >
              <option value="weighted-median">Weighted Median</option>
              <option value="mean">Mean</option>
              <option value="median">Median</option>
            </select>
          </div>

          {/* Trigger conditions */}
          <div>
            <span className="text-sm font-medium text-stone-700 block mb-3">
              Trigger conditions
            </span>
            <div className="space-y-2.5">
              {[
                { key: "always" as const, label: "Always" },
                { key: "manualOnly" as const, label: "Manual only" },
                { key: "highStakes" as const, label: "High-stakes content" },
                { key: "lowConfidence" as const, label: "Low confidence scores" },
                { key: "failedThreshold" as const, label: "Failed quality threshold" },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={conditions[key]}
                    onChange={() => toggleCondition(key)}
                    className="w-4 h-4 rounded border-stone-300 text-brand-500 focus:ring-brand-500/20"
                    style={{ accentColor: "#C65D3B" }}
                  />
                  <span className="text-sm text-stone-700">{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {onSave && (
        <div className="mt-5 pt-4 border-t border-stone-100">
          <button
            type="button"
            disabled={saving}
            onClick={async () => {
              setSaving(true);
              setSaved(false);
              try {
                const triggerConditionsList: string[] = [];
                if (conditions.always) triggerConditionsList.push("always");
                if (conditions.manualOnly) triggerConditionsList.push("manual_only");
                if (conditions.highStakes) triggerConditionsList.push("high_stakes");
                if (conditions.lowConfidence) triggerConditionsList.push("low_confidence");
                if (conditions.failedThreshold) triggerConditionsList.push("failed_threshold");
                await onSave({
                  enabled,
                  min_models: minModels,
                  consensus_method: consensus,
                  trigger_conditions: triggerConditionsList,
                });
                setSaved(true);
                setTimeout(() => setSaved(false), 2000);
              } finally {
                setSaving(false);
              }
            }}
            className="bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : saved ? "Saved" : "Save Config"}
          </button>
        </div>
      )}
    </div>
  );
}
