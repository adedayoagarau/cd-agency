"use client";

import { useState, useCallback } from "react";
import { Download } from "lucide-react";
import { BrandUpload } from "@/components/brand-dna/brand-upload";
import { VoicePatternsTab } from "@/components/brand-dna/voice-patterns-tab";
import { TerminologyTab } from "@/components/brand-dna/terminology-tab";
import { StyleRulesTab } from "@/components/brand-dna/style-rules-tab";
import { SourcesTab } from "@/components/brand-dna/sources-tab";
import { useBrandDNA } from "@/lib/hooks";
import { api, type BrandDNAData } from "@/lib/api";

const tabs = [
  { id: "voice", label: "Voice Patterns" },
  { id: "terminology", label: "Terminology" },
  { id: "style", label: "Style Rules" },
  { id: "sources", label: "Sources" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function BrandDnaPage() {
  const [activeTab, setActiveTab] = useState<TabId>("voice");
  const { data: brandDNA, loading, error, refetch } = useBrandDNA();
  const isLive = !!brandDNA && !error;

  const handleSave = useCallback(async (update: Partial<BrandDNAData>) => {
    await api.updateBrandDNA(update);
    await refetch();
  }, [refetch]);

  const handleIngest = useCallback(async (content: string) => {
    await api.ingestBrandContent(content);
    await refetch();
  }, [refetch]);

  const handleExport = useCallback(() => {
    if (!brandDNA) return;
    const exportData = {
      voice_patterns: brandDNA.voice_patterns,
      terminology: brandDNA.terminology,
      style_rules: brandDNA.style_rules,
      sources: brandDNA.sources,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "brand-dna-export.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [brandDNA]);

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-serif text-2xl font-semibold text-stone-900">
              Brand DNA
            </h1>
            {!loading && (
              <span className={`inline-flex items-center gap-1.5 text-xs ${isLive ? 'text-emerald-600' : 'text-amber-600'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                {isLive ? 'Live' : 'Demo data'}
              </span>
            )}
          </div>
          <p className="text-stone-500 mt-1">
            Your brand&apos;s voice, terminology, and style rules that all
            agents follow.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExport}
            disabled={!brandDNA}
            className="inline-flex items-center gap-2 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm font-medium text-stone-700 shadow-sm transition-colors hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Export Brand DNA
          </button>
          <BrandUpload onIngest={handleIngest} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-stone-200 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
              activeTab === tab.id
                ? "border-b-2 border-brand-500 text-brand-700"
                : "text-stone-500 hover:text-stone-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "voice" && <VoicePatternsTab data={brandDNA?.voice_patterns} onSave={(patterns) => handleSave({ voice_patterns: patterns })} />}
      {activeTab === "terminology" && <TerminologyTab data={brandDNA?.terminology} onSave={(terminology) => handleSave({ terminology })} />}
      {activeTab === "style" && <StyleRulesTab data={brandDNA?.style_rules} onSave={(style_rules) => handleSave({ style_rules })} />}
      {activeTab === "sources" && <SourcesTab data={brandDNA?.sources} />}
    </div>
  );
}
