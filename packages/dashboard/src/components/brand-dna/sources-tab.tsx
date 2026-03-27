"use client";

import { Link, Upload, Plus } from "lucide-react";
import { sources as mockSources } from "@/lib/data/brand-dna";

interface SourcesTabProps {
  data?: string[];
}

const typeBadgeColors: Record<string, string> = {
  PDF: "bg-rose-50 text-rose-700 border-rose-100",
  Doc: "bg-blue-50 text-blue-700 border-blue-100",
  URL: "bg-emerald-50 text-emerald-700 border-emerald-100",
};

export function SourcesTab({ data }: SourcesTabProps) {
  // API returns string[] while mock data has richer objects.
  // When API data is available, map strings to a display-friendly format;
  // otherwise fall back to the full mock data.
  const sources = data
    ? data.map((name, i) => ({
        id: i + 1,
        filename: name,
        type: name.endsWith(".pdf") ? "PDF" : name.startsWith("http") ? "URL" : "Doc",
        extractedDate: "Via API",
        patternsExtracted: 0,
      }))
    : mockSources;
  return (
    <div>
      {/* Upload area */}
      <div className="border-2 border-dashed border-stone-200 rounded-xl p-8 text-center hover:border-brand-300 transition-colors cursor-pointer mb-6">
        <div className="flex flex-col items-center gap-2">
          <div className="w-10 h-10 rounded-lg bg-stone-100 flex items-center justify-center">
            <Upload className="w-5 h-5 text-stone-400" />
          </div>
          <p className="text-sm text-stone-600">
            Drop brand documents here or click to browse
          </p>
          <p className="text-xs text-stone-400">.pdf, .docx, .txt, .md</p>
        </div>
      </div>

      {/* Extract from CMS button */}
      <button
        type="button"
        className="mb-6 inline-flex items-center gap-2 text-sm text-stone-600 border border-stone-200 rounded-lg px-4 py-2 hover:bg-stone-50 transition-colors"
      >
        <Link className="w-4 h-4" />
        Extract from CMS
      </button>

      {/* Sources list */}
      <div className="bg-white rounded-xl border border-stone-100 overflow-hidden">
        {sources.map((source, index) => (
          <div
            key={source.id}
            className={`flex items-center justify-between px-5 py-4 hover:bg-stone-50 transition-colors ${
              index < sources.length - 1 ? "border-b border-stone-50" : ""
            }`}
          >
            <div className="flex items-center gap-3">
              <span
                className={`text-[10px] uppercase font-bold rounded-full px-2 py-0.5 border ${typeBadgeColors[source.type] || "bg-stone-50 text-stone-700 border-stone-100"}`}
              >
                {source.type}
              </span>
              <div>
                <p className="text-sm font-medium text-stone-800">
                  {source.filename}
                </p>
                <p className="text-xs text-stone-400">
                  Extracted {source.extractedDate}
                </p>
              </div>
            </div>
            <span className="text-xs text-stone-500">
              {source.patternsExtracted} patterns
            </span>
          </div>
        ))}
      </div>

      {/* Add source button */}
      <button
        type="button"
        className="mt-4 text-sm text-brand-600 border border-dashed border-brand-200 rounded-lg p-2 w-full flex items-center justify-center gap-1.5 hover:bg-brand-50 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add source
      </button>
    </div>
  );
}
