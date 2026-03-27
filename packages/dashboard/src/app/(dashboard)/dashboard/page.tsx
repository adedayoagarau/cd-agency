"use client";

import { Greeting } from "@/components/dashboard/greeting";
import { QuickRunCard } from "@/components/dashboard/quick-run-card";
import { BrandHealthCard } from "@/components/dashboard/brand-health-card";
import { UsageCard } from "@/components/dashboard/usage-card";
import { PlatformsCard } from "@/components/dashboard/platforms-card";
import { RecentRuns } from "@/components/dashboard/recent-runs";
import { TeamActivity } from "@/components/dashboard/team-activity";
import { useAgents, useHistory, useConnectors } from "@/lib/hooks";

export default function DashboardPage() {
  const { data: apiAgents, error: apiError } = useAgents();
  const { data: _history } = useHistory();
  const { data: _connectors } = useConnectors();
  const isLive = !!apiAgents && !apiError;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Greeting name="Alex" />
        <span className={`inline-flex items-center gap-1.5 text-xs ${isLive ? 'text-emerald-600' : 'text-amber-600'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          {isLive ? 'Connected to backend' : 'Demo mode'}
        </span>
      </div>
      {/* QuickRunCard: ready for API data — pass apiAgents when agent select is wired */}
      <QuickRunCard />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <BrandHealthCard />
        <UsageCard />
        <PlatformsCard />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <RecentRuns className="col-span-1 md:col-span-2" />
        <TeamActivity className="col-span-1" />
      </div>
    </div>
  );
}
