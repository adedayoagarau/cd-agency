"use client";

import { Connector } from "@/lib/data/connectors";

const iconBgMap: Record<string, { bg: string; label: string }> = {
  sanity: { bg: "bg-rose-500", label: "Sa" },
  strapi: { bg: "bg-indigo-500", label: "St" },
  wordpress: { bg: "bg-sky-700", label: "Wp" },
  storyblok: { bg: "bg-teal-500", label: "Sb" },
  airtable: { bg: "bg-yellow-500", label: "At" },
  "google-docs": { bg: "bg-blue-500", label: "Gd" },
  markdown: { bg: "bg-stone-700", label: "Md" },
  slack: { bg: "bg-purple-500", label: "Sl" },
  github: { bg: "bg-stone-900", label: "Gh" },
  linear: { bg: "bg-indigo-600", label: "Li" },
  webflow: { bg: "bg-blue-600", label: "Wf" },
  datocms: { bg: "bg-orange-500", label: "Da" },
};

function ContentfulIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <rect x="4" y="4" width="14" height="14" rx="3" fill="#3B82F6" />
      <rect x="22" y="4" width="14" height="14" rx="3" fill="#60A5FA" />
      <rect x="4" y="22" width="14" height="14" rx="3" fill="#93C5FD" />
      <rect x="22" y="22" width="14" height="14" rx="3" fill="#3B82F6" />
    </svg>
  );
}

function FigmaIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
      <path d="M14 36c3.3 0 6-2.7 6-6v-6h-6c-3.3 0-6 2.7-6 6s2.7 6 6 6z" fill="#0ACF83" />
      <path d="M8 18c0-3.3 2.7-6 6-6h6v12h-6c-3.3 0-6-2.7-6-6z" fill="#A259FF" />
      <path d="M8 6c0-3.3 2.7-6 6-6h6v12h-6C10.7 12 8 9.3 8 6z" fill="#F24E1E" />
      <path d="M20 0h6c3.3 0 6 2.7 6 6s-2.7 6-6 6h-6V0z" fill="#FF7262" />
      <path d="M32 18c0 3.3-2.7 6-6 6s-6-2.7-6-6 2.7-6 6-6 6 2.7 6 6z" fill="#1ABCFE" />
    </svg>
  );
}

function NotionIcon() {
  return (
    <div className="w-10 h-10 rounded-lg border-2 border-stone-800 flex items-center justify-center">
      <span className="font-serif text-lg font-bold text-stone-800">N</span>
    </div>
  );
}

function ConnectorIcon({ icon }: { icon: string }) {
  if (icon === "contentful") return <ContentfulIcon />;
  if (icon === "figma") return <FigmaIcon />;
  if (icon === "notion") return <NotionIcon />;

  const mapping = iconBgMap[icon];
  if (mapping) {
    return (
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm ${mapping.bg}`}>
        {mapping.label}
      </div>
    );
  }

  return (
    <div className="w-10 h-10 rounded-lg bg-stone-400 flex items-center justify-center text-white font-bold text-sm">
      {icon.charAt(0).toUpperCase()}
    </div>
  );
}

interface ConnectorCardProps {
  connector: Connector;
  onSettings?: () => void;
  onSync?: (name: string) => void;
  onConnect?: (name: string) => void;
}

export function ConnectorCard({ connector, onSettings, onSync, onConnect }: ConnectorCardProps) {
  if (connector.status === "connected") {
    return (
      <div className="bg-surface-card rounded-xl p-6 shadow-soft border-l-4 border-emerald-400">
        <ConnectorIcon icon={connector.icon} />
        <h3 className="text-base font-medium text-stone-800 mt-3 mb-1">{connector.name}</h3>
        <div className="flex items-center gap-1.5 mb-2">
          <span className="w-2 h-2 bg-emerald-500 rounded-full" />
          <span className="text-sm text-emerald-600">Connected</span>
        </div>
        <p className="text-xs text-stone-400 mb-1">Last sync: {connector.lastSync}</p>
        <p className="text-xs text-stone-400 mb-4">
          {connector.entries?.toLocaleString()} entries &middot; {connector.contentTypes} types
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onSync?.(connector.name)}
            className="bg-white border border-stone-200 text-sm px-3 py-1.5 rounded-md text-stone-600 hover:bg-stone-50 transition-colors"
          >
            Sync Now
          </button>
          <button
            type="button"
            onClick={onSettings}
            className="bg-white border border-stone-200 text-sm px-3 py-1.5 rounded-md text-stone-600 hover:bg-stone-50 transition-colors"
          >
            Settings
          </button>
        </div>
      </div>
    );
  }

  if (connector.status === "available") {
    return (
      <div className="bg-surface-card rounded-xl p-6 shadow-soft border border-stone-200">
        <ConnectorIcon icon={connector.icon} />
        <h3 className="text-base font-medium text-stone-800 mt-3 mb-1">{connector.name}</h3>
        <p className="text-sm text-stone-500 mb-1">Available</p>
        <p className="text-xs text-stone-400 mb-4">{connector.description}</p>
        <button
          type="button"
          onClick={() => onConnect?.(connector.name)}
          className="bg-brand-500 text-white text-sm px-4 py-1.5 rounded-md hover:bg-brand-600 transition-colors"
        >
          Connect
        </button>
      </div>
    );
  }

  // coming-soon
  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft border border-stone-200 opacity-60">
      <div className="flex items-start justify-between">
        <ConnectorIcon icon={connector.icon} />
        <span className="bg-stone-100 text-stone-500 text-[10px] uppercase font-bold rounded-full px-2 py-0.5">
          Coming soon
        </span>
      </div>
      <h3 className="text-base font-medium text-stone-800 mt-3 mb-1">{connector.name}</h3>
      <p className="text-xs text-stone-400 mb-3">{connector.description}</p>
      <button type="button" className="text-xs text-brand-600 hover:text-brand-700 transition-colors">
        Notify me
      </button>
    </div>
  );
}
