"use client";

import { Upload } from "lucide-react";

interface StepOptionalProps {
  onFinish: () => void;
}

export function StepOptional({ onFinish }: StepOptionalProps) {
  return (
    <div className="flex flex-col">
      <h1 className="font-serif text-2xl text-center text-stone-900">
        Supercharge your workspace
      </h1>

      {/* Option cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        {/* Connect your CMS */}
        <div className="bg-surface-card rounded-xl p-6 border border-stone-200 text-center">
          <p className="text-sm font-medium text-stone-900 mb-3">Connect your CMS</p>
          <div className="flex items-center justify-center gap-3 mb-3">
            {/* Contentful */}
            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <circle cx="4" cy="4" r="2" fill="#0681E0" />
                <circle cx="4" cy="12" r="2" fill="#FAD338" />
                <circle cx="12" cy="8" r="2" fill="#EB5A68" />
                <path d="M5.5 4.5C7 5.5 7 10.5 5.5 11.5" stroke="#0681E0" strokeWidth="1.5" fill="none" />
              </svg>
            </div>
            {/* Figma */}
            <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center">
              <svg width="12" height="16" viewBox="0 0 12 16" fill="none" aria-hidden="true">
                <path d="M3 16c1.657 0 3-1.343 3-3v-3H3c-1.657 0-3 1.343-3 3s1.343 3 3 3z" fill="#0ACF83" />
                <path d="M0 8c0-1.657 1.343-3 3-3h3v6H3c-1.657 0-3-1.343-3-3z" fill="#A259FF" />
                <path d="M0 3c0-1.657 1.343-3 3-3h3v6H3C1.343 6 0 4.657 0 3z" fill="#F24E1E" />
                <path d="M6 0h3c1.657 0 3 1.343 3 3s-1.343 3-3 3H6V0z" fill="#FF7262" />
                <circle cx="9" cy="8" r="3" fill="#1ABCFE" />
              </svg>
            </div>
            {/* Notion */}
            <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center">
              <span className="text-stone-900 font-serif text-sm font-bold">N</span>
            </div>
          </div>
          <button className="border border-brand-200 text-brand-600 rounded-lg px-4 py-2 text-sm font-medium hover:bg-brand-50 transition-colors">
            Connect
          </button>
        </div>

        {/* Teach it your brand */}
        <div className="bg-surface-card rounded-xl p-6 border border-stone-200 text-center">
          <p className="text-sm font-medium text-stone-900 mb-3">Teach it your brand</p>
          <div className="flex items-center justify-center mb-3">
            <Upload size={32} className="text-brand-400" />
          </div>
          <button className="border border-brand-200 text-brand-600 rounded-lg px-4 py-2 text-sm font-medium hover:bg-brand-50 transition-colors">
            Upload Brand Guide
          </button>
        </div>
      </div>

      {/* Skip for now */}
      <a
        href="#"
        onClick={(e) => {
          e.preventDefault();
          onFinish();
        }}
        className="text-sm text-stone-400 hover:text-stone-600 text-center mt-4 block transition-colors"
      >
        Skip for now
      </a>

      {/* Go to Dashboard */}
      <button
        onClick={onFinish}
        className="bg-brand-500 text-white w-full h-11 rounded-xl mt-6 text-sm font-medium hover:bg-brand-600 transition-colors"
      >
        Go to Dashboard
      </button>
    </div>
  );
}
