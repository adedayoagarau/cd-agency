"use client";

import { useState, useMemo } from "react";
import { useConnectors } from "@/lib/hooks";
import { api } from "@/lib/api";
import { connectors as mockConnectors, Connector, ConnectorStatus } from "@/lib/data/connectors";
import { ConnectorCard } from "@/components/connectors/connector-card";
import { ConnectorDetailSheet } from "@/components/connectors/connector-detail-sheet";

type FilterType = "all" | ConnectorStatus;

const filters: { label: string; value: FilterType }[] = [
  { label: "All", value: "all" },
  { label: "Connected", value: "connected" },
  { label: "Available", value: "available" },
  { label: "Coming Soon", value: "coming-soon" },
];

export default function ConnectorsPage() {
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null);

  const { data: apiConnectors, loading, refetch } = useConnectors();

  const handleSync = async (name: string) => {
    await api.syncConnector(name);
    refetch();
  };

  const handleDisconnect = async (name: string) => {
    await api.disconnectConnector(name);
    setSelectedConnector(null);
    refetch();
  };

  const isLive = !!(apiConnectors && apiConnectors.length > 0);

  const connectorList = useMemo(() => {
    if (apiConnectors && apiConnectors.length > 0) {
      // Map API connectors and merge with mock data for UI-only fields
      return mockConnectors.map((mock) => {
        const live = apiConnectors.find((c) => c.name.toLowerCase() === mock.id);
        if (live) {
          return {
            ...mock,
            status: "connected" as const,
            lastSync: live.last_sync || mock.lastSync,
            entries: live.entry_count || mock.entries,
          };
        }
        return mock;
      });
    }
    return mockConnectors;
  }, [apiConnectors]);

  const filtered = useMemo(() => {
    if (activeFilter === "all") return connectorList;
    return connectorList.filter((c) => c.status === activeFilter);
  }, [activeFilter, connectorList]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="font-serif text-2xl font-semibold text-stone-900">Connectors</h1>
          <span className="flex items-center gap-1 text-xs text-stone-400">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${
                isLive ? "bg-emerald-500" : "bg-amber-400"
              }`}
            />
            {isLive ? "Live" : "Demo data"}
          </span>
        </div>
        <p className="text-stone-500 mt-1">Connect your content platforms to cd-agency.</p>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="text-sm text-stone-400 animate-pulse">Loading connectors...</div>
      )}

      {/* Filter pills */}
      <div className="flex items-center gap-2">
        {filters.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setActiveFilter(f.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              activeFilter === f.value
                ? "bg-brand-50 text-brand-700 border-brand-200"
                : "bg-white text-stone-500 border-stone-200 hover:bg-stone-50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((connector) => (
          <ConnectorCard
            key={connector.id}
            connector={connector}
            onSettings={() => setSelectedConnector(connector)}
            onSync={handleSync}
            onConnect={handleSync}
          />
        ))}
      </div>

      {/* Detail sheet */}
      <ConnectorDetailSheet
        connector={selectedConnector}
        onClose={() => setSelectedConnector(null)}
        onSync={handleSync}
        onDisconnect={handleDisconnect}
      />
    </div>
  );
}
