"use client";

import { useState } from "react";
import { Globe, Loader2, Dna, ExternalLink } from "lucide-react";
import { api, type ScrapeResult } from "@/lib/api";

export default function ScrapePage() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<ScrapeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [ingested, setIngested] = useState(false);

  const handleScrape = async () => {
    if (!url.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setIngested(false);
    try {
      const res = await api.scrapeUrl(url);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleIngestAsBrandDNA = async () => {
    if (!result?.raw_text || ingesting) return;
    setIngesting(true);
    try {
      await api.ingestBrandContent(result.raw_text);
      setIngested(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">Scrape</h1>
        <p className="text-sm text-stone-500 mt-1">
          Extract structured content from any web page for analysis or Brand DNA ingestion.
        </p>
      </div>

      {/* URL input */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <label htmlFor="scrape-url" className="block text-sm font-medium text-stone-700 mb-2">
          Page URL
        </label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
            <input
              id="scrape-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleScrape()}
              placeholder="https://example.com/about"
              className="w-full bg-white border border-stone-200 text-stone-800 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
          </div>
          <button
            onClick={handleScrape}
            disabled={loading || !url.trim()}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors inline-flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Scraping...
              </>
            ) : (
              "Scrape"
            )}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Title & description */}
          <div className="bg-surface-card rounded-xl p-6 shadow-soft">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-serif text-lg font-semibold text-stone-900">
                {result.title || "Untitled Page"}
              </h2>
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-brand-600 hover:text-brand-700 inline-flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Open
              </a>
            </div>
            {result.description && (
              <p className="text-sm text-stone-600 mb-4">{result.description}</p>
            )}

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleIngestAsBrandDNA}
                disabled={ingesting || ingested}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 transition-colors disabled:opacity-50"
              >
                <Dna className="w-4 h-4" />
                {ingested ? "Added to Brand DNA" : ingesting ? "Ingesting..." : "Use as Brand DNA Source"}
              </button>
            </div>
          </div>

          {/* Headings */}
          {result.headings.length > 0 && (
            <div className="bg-surface-card rounded-xl p-6 shadow-soft">
              <h3 className="text-sm font-semibold text-stone-700 mb-3">Headings</h3>
              <ul className="space-y-1.5">
                {result.headings.map((h, i) => (
                  <li key={i} className="text-sm text-stone-600">
                    <span className="text-stone-400 font-mono text-xs mr-2">
                      {h.split(":")[0]}
                    </span>
                    {h.split(":").slice(1).join(":").trim()}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Body text */}
          {result.paragraphs.length > 0 && (
            <div className="bg-surface-card rounded-xl p-6 shadow-soft">
              <h3 className="text-sm font-semibold text-stone-700 mb-3">
                Body Text ({result.paragraphs.length} paragraphs)
              </h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {result.paragraphs.map((p, i) => (
                  <p key={i} className="text-sm text-stone-600 leading-relaxed">{p}</p>
                ))}
              </div>
            </div>
          )}

          {/* Meta tags */}
          {Object.keys(result.meta).length > 0 && (
            <div className="bg-surface-card rounded-xl p-6 shadow-soft">
              <h3 className="text-sm font-semibold text-stone-700 mb-3">Meta Tags</h3>
              <div className="space-y-2">
                {Object.entries(result.meta).map(([key, value]) => (
                  <div key={key} className="flex gap-3 text-sm">
                    <span className="text-stone-400 font-mono text-xs min-w-[140px] shrink-0">{key}</span>
                    <span className="text-stone-600 line-clamp-2">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
