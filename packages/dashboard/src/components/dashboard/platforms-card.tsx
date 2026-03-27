import { Link, Plus } from "lucide-react";

function CheckmarkBadge() {
  return (
    <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-full flex items-center justify-center">
      <svg
        viewBox="0 0 12 12"
        fill="none"
        className="w-2 h-2"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M3 6.5L5 8.5L9 4"
          stroke="white"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

function ContentfulIcon() {
  return (
    <div className="relative w-12 h-12 rounded-xl border border-stone-200 shadow-sm flex items-center justify-center bg-white hover:-translate-y-1 transition-transform cursor-pointer">
      <CheckmarkBadge />
      <svg
        viewBox="0 0 24 24"
        width="20"
        height="20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect x="3" y="3" width="7" height="7" rx="1" fill="#3B82F6" />
        <rect x="14" y="3" width="7" height="7" rx="1" fill="#3B82F6" />
        <rect x="3" y="14" width="7" height="7" rx="1" fill="#3B82F6" />
        <rect x="14" y="14" width="7" height="7" rx="1" fill="#3B82F6" opacity="0.4" />
      </svg>
    </div>
  );
}

function FigmaIcon() {
  return (
    <div className="relative w-12 h-12 rounded-xl border border-stone-200 shadow-sm flex items-center justify-center bg-white hover:-translate-y-1 transition-transform cursor-pointer">
      <CheckmarkBadge />
      <svg
        viewBox="0 0 38 57"
        width="20"
        height="20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M19 28.5a9.5 9.5 0 1 1 19 0 9.5 9.5 0 0 1-19 0z"
          fill="#1ABCFE"
        />
        <path
          d="M0 47.5a9.5 9.5 0 0 1 9.5-9.5H19v9.5a9.5 9.5 0 1 1-19 0z"
          fill="#0ACF83"
        />
        <path
          d="M19 0v19h9.5a9.5 9.5 0 1 0 0-19H19z"
          fill="#FF7262"
        />
        <path
          d="M0 9.5A9.5 9.5 0 0 0 9.5 19H19V0H9.5A9.5 9.5 0 0 0 0 9.5z"
          fill="#F24E1E"
        />
        <path
          d="M0 28.5A9.5 9.5 0 0 0 9.5 38H19V19H9.5A9.5 9.5 0 0 0 0 28.5z"
          fill="#A259FF"
        />
      </svg>
    </div>
  );
}

function NotionIcon() {
  return (
    <div className="relative w-12 h-12 rounded-xl border border-stone-200 shadow-sm flex items-center justify-center bg-white hover:-translate-y-1 transition-transform cursor-pointer">
      <CheckmarkBadge />
      <span className="text-stone-900 font-serif text-lg font-bold">N</span>
    </div>
  );
}

export function PlatformsCard() {
  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft flex flex-col justify-between min-h-[180px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Link className="w-4 h-4 text-brand-400" />
          <span className="text-sm font-medium text-stone-600">Connected Platforms</span>
        </div>
        <a
          href="#"
          className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors"
        >
          Manage
        </a>
      </div>

      {/* Platform icons */}
      <div className="flex items-center gap-4 mb-4">
        <ContentfulIcon />
        <FigmaIcon />
        <NotionIcon />
        <button
          type="button"
          className="w-12 h-12 rounded-xl border border-dashed border-stone-300 flex items-center justify-center text-stone-400 hover:text-brand-500 hover:border-brand-300 hover:bg-brand-50 transition-colors cursor-pointer"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Footer */}
      <p className="text-sm text-stone-500 mt-auto pt-2">
        3 active &mdash; all syncing smoothly
      </p>
    </div>
  );
}
