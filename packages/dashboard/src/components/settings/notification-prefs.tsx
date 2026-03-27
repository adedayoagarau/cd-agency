"use client";

import { useState } from "react";

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${
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

interface NotificationRow {
  key: string;
  label: string;
  defaultOn: boolean;
}

const notifications: NotificationRow[] = [
  { key: "agent-failures", label: "Agent run failures", defaultOn: true },
  { key: "sync-errors", label: "Connector sync errors", defaultOn: true },
  { key: "usage-limit", label: "Usage approaching limit", defaultOn: true },
  { key: "weekly-summary", label: "Weekly summary", defaultOn: false },
  { key: "team-joined", label: "Team member joined", defaultOn: true },
];

export function NotificationPrefs() {
  const [prefs, setPrefs] = useState<Record<string, boolean>>(
    Object.fromEntries(notifications.map((n) => [n.key, n.defaultOn]))
  );

  function toggle(key: string) {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft">
      <h3 className="text-base font-semibold text-stone-900 mb-4">
        Notifications
      </h3>

      <div>
        {notifications.map((n, idx) => (
          <div
            key={n.key}
            className={`flex items-center justify-between py-3 ${
              idx < notifications.length - 1 ? "border-b border-stone-100" : ""
            }`}
          >
            <span className="text-sm text-stone-700">{n.label}</span>
            <Toggle enabled={prefs[n.key]} onChange={() => toggle(n.key)} />
          </div>
        ))}
      </div>
    </div>
  );
}
