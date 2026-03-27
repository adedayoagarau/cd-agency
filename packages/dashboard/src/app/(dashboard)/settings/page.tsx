"use client";

import { useState, useCallback } from "react";
import { Upload } from "lucide-react";
import { QualityThresholds } from "@/components/settings/quality-thresholds";
import { CouncilConfig } from "@/components/settings/council-config";
import { NotificationPrefs } from "@/components/settings/notification-prefs";
import { useQualityThresholds, useCouncilStatus } from "@/lib/hooks";
import { api, type CouncilStatusData } from "@/lib/api";

export default function SettingsPage() {
  const [orgName, setOrgName] = useState("Acme Corp");
  const { data: thresholds, refetch: refetchThresholds } = useQualityThresholds();
  const { data: council, refetch: refetchCouncil } = useCouncilStatus();

  const handleSaveThresholds = useCallback(async (updated: Record<string, number>) => {
    await api.updateQualityThresholds(updated);
    await refetchThresholds();
  }, [refetchThresholds]);

  const handleSaveCouncil = useCallback(async (config: CouncilStatusData) => {
    await api.updateCouncilConfig(config);
    await refetchCouncil();
  }, [refetchCouncil]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">
          Settings
        </h1>
        <p className="text-sm text-stone-500 mt-1">
          Configure your organization and workspace preferences.
        </p>
      </div>

      {/* Section 1: Organization */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h3 className="text-base font-semibold text-stone-900 mb-4">
          Organization
        </h3>

        <div className="space-y-4">
          {/* Org name */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">
              Organization name
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              className="w-full max-w-sm border border-stone-200 rounded-lg px-3 py-2 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
          </div>

          {/* Org slug */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">
              Organization slug
            </label>
            <input
              type="text"
              value="acme-corp"
              readOnly
              className="w-full max-w-sm bg-stone-50 text-stone-400 border border-stone-200 rounded-lg px-3 py-2 text-sm cursor-not-allowed"
            />
          </div>

          {/* Logo upload */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">
              Logo
            </label>
            <div className="w-16 h-16 border-2 border-dashed border-stone-300 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:border-stone-400 transition-colors">
              <Upload className="w-5 h-5 text-stone-400" />
              <span className="text-[10px] text-stone-400 mt-0.5">Upload logo</span>
            </div>
          </div>

          <div className="flex items-center mt-4">
            <button className="bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors">
              Save changes
            </button>
            <button
              onClick={() => {
                localStorage.removeItem("cd-agency-onboarding-complete");
                window.location.href = "/onboarding";
              }}
              className="text-stone-500 border border-stone-200 px-4 py-2 rounded-lg text-sm font-medium hover:bg-stone-50 transition-colors ml-3"
            >
              Restart Onboarding
            </button>
          </div>
        </div>
      </div>

      {/* Section 2: Quality Thresholds */}
      <QualityThresholds initialData={thresholds} onSave={handleSaveThresholds} />

      {/* Section 3: Council Configuration */}
      <CouncilConfig initialData={council} onSave={handleSaveCouncil} />

      {/* Section 4: Notifications */}
      <NotificationPrefs />

      {/* Section 5: Danger Zone */}
      <div className="border border-rose-200 rounded-xl p-6 bg-rose-50/30">
        <h3 className="text-base font-semibold text-rose-700">
          Delete organization
        </h3>
        <p className="text-sm text-rose-600/80 mt-1">
          This will permanently delete your workspace, all agents, Brand DNA,
          memory, and connector configurations. This action cannot be undone.
        </p>
        <button className="bg-rose-600 text-white px-4 py-2 rounded-lg text-sm font-medium mt-3 hover:bg-rose-700 transition-colors">
          Delete Acme Corp
        </button>
      </div>
    </div>
  );
}
