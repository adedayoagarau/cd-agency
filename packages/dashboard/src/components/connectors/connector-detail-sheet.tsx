"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { Connector } from "@/lib/data/connectors";

interface ConnectorDetailSheetProps {
  connector: Connector | null;
  onClose: () => void;
  onSync?: (name: string) => void;
  onDisconnect?: (name: string) => void;
}

const syncHistory = [
  { time: "Today, 10:32 AM", detail: "Synced 24 entries, 2 content types updated" },
  { time: "Today, 10:17 AM", detail: "Synced 12 entries, no changes" },
  { time: "Yesterday, 4:45 PM", detail: "Synced 47 entries, 1 asset updated" },
];

export function ConnectorDetailSheet({ connector, onClose, onSync, onDisconnect }: ConnectorDetailSheetProps) {
  const [interval, setInterval] = useState("15m");
  const [syncEntries, setSyncEntries] = useState(true);
  const [syncAssets, setSyncAssets] = useState(true);
  const [syncTypes, setSyncTypes] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    if (!connector || !onSync) return;
    setSyncing(true);
    try {
      await onSync(connector.name);
    } finally {
      setSyncing(false);
    }
  };

  if (!connector) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />

      {/* Panel */}
      <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl z-50 flex flex-col overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <h2 className="font-serif text-lg font-semibold text-stone-800">{connector.name}</h2>
            {connector.status === "connected" && (
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                Connected
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Connection status */}
        <div className="p-6 border-b border-stone-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-stone-700">Connection Status</h3>
            {syncing && (
              <span className="inline-flex items-center gap-1.5 text-xs text-brand-600">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Syncing...
              </span>
            )}
          </div>
          <div className="bg-stone-50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-stone-500">Last sync</span>
              <span className="text-stone-800 font-medium">{connector.lastSync || "Never"}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-stone-500">Entries</span>
              <span className="text-stone-800 font-medium">{connector.entries?.toLocaleString() || "0"}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-stone-500">Content types</span>
              <span className="text-stone-800 font-medium">{connector.contentTypes || "0"}</span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            className="mt-3 w-full bg-white border border-stone-200 text-sm px-3 py-1.5 rounded-md text-stone-600 hover:bg-stone-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing ? "Syncing..." : "Sync Now"}
          </button>
        </div>

        {/* Sync settings */}
        <div className="p-6 border-b border-stone-100">
          <h3 className="text-sm font-medium text-stone-700 mb-3">Sync Settings</h3>

          <label className="block text-xs text-stone-500 mb-1">Interval</label>
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="w-full bg-white border border-stone-200 rounded-lg px-3 py-2 text-sm text-stone-700 mb-4 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
          >
            <option value="5m">Every 5 minutes</option>
            <option value="15m">Every 15 minutes</option>
            <option value="30m">Every 30 minutes</option>
            <option value="1h">Every 1 hour</option>
            <option value="6h">Every 6 hours</option>
          </select>

          <p className="text-xs text-stone-500 mb-2">What to sync</p>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
              <input
                type="checkbox"
                checked={syncEntries}
                onChange={(e) => setSyncEntries(e.target.checked)}
                className="rounded border-stone-300 text-brand-500 focus:ring-brand-500"
              />
              Content entries
            </label>
            <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
              <input
                type="checkbox"
                checked={syncAssets}
                onChange={(e) => setSyncAssets(e.target.checked)}
                className="rounded border-stone-300 text-brand-500 focus:ring-brand-500"
              />
              Assets
            </label>
            <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
              <input
                type="checkbox"
                checked={syncTypes}
                onChange={(e) => setSyncTypes(e.target.checked)}
                className="rounded border-stone-300 text-brand-500 focus:ring-brand-500"
              />
              Content types
            </label>
          </div>
        </div>

        {/* Sync history */}
        <div className="p-6 border-b border-stone-100 flex-1">
          <h3 className="text-sm font-medium text-stone-700 mb-3">Sync History</h3>
          <div className="space-y-3">
            {syncHistory.map((entry, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-medium text-stone-600">{entry.time}</p>
                  <p className="text-xs text-stone-400">{entry.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Disconnect */}
        <div className="p-6">
          <button
            type="button"
            onClick={() => onDisconnect?.(connector.name)}
            className="w-full text-rose-600 border border-rose-200 rounded-lg py-2 hover:bg-rose-50 transition-colors text-sm font-medium"
          >
            Disconnect
          </button>
        </div>
      </div>
    </>
  );
}
