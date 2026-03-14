import { useState } from "react";
import { useStore } from "../store";
import { scrapeUrl } from "../api";
import type { ScrapeResponse } from "../types";

export function ScrapePanel() {
  const { loading, setLoading, setError, setTab } = useStore();
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<ScrapeResponse | null>(null);

  const handleScrape = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await scrapeUrl(url.trim());
      setResult(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleScrape();
    }
  };

  const handleSendToForm = () => {
    if (result?.raw_text) {
      navigator.clipboard.writeText(result.raw_text);
      setTab("form");
    }
  };

  return (
    <div className="panel scrape-panel">
      <div className="scrape-input-bar">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="https://example.com/page-to-scrape"
          className="scrape-url-input"
        />
        <button
          className="btn btn-primary"
          onClick={handleScrape}
          disabled={!url.trim() || loading}
        >
          {loading ? "Scraping..." : "Scrape"}
        </button>
      </div>

      {result && (
        <div className="scrape-results">
          <div className="scrape-actions">
            <button className="btn btn-sm" onClick={() => navigator.clipboard.writeText(result.raw_text)}>
              Copy Text
            </button>
            <button className="btn btn-sm btn-primary" onClick={handleSendToForm}>
              Send to Form
            </button>
          </div>

          {result.title && (
            <div className="scrape-section">
              <div className="scrape-section-title">Title</div>
              <div className="scrape-section-content">{result.title}</div>
            </div>
          )}

          {result.description && (
            <div className="scrape-section">
              <div className="scrape-section-title">Description</div>
              <div className="scrape-section-content">{result.description}</div>
            </div>
          )}

          {result.headings.length > 0 && (
            <div className="scrape-section">
              <div className="scrape-section-title">Headings ({result.headings.length})</div>
              <ul className="scrape-list">
                {result.headings.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </div>
          )}

          {result.paragraphs.length > 0 && (
            <div className="scrape-section">
              <div className="scrape-section-title">Paragraphs ({result.paragraphs.length})</div>
              {result.paragraphs.slice(0, 10).map((p, i) => (
                <p key={i} className="scrape-paragraph">{p}</p>
              ))}
              {result.paragraphs.length > 10 && (
                <div className="score-detail">...and {result.paragraphs.length - 10} more</div>
              )}
            </div>
          )}

          {result.links.length > 0 && (
            <div className="scrape-section">
              <div className="scrape-section-title">Links ({result.links.length})</div>
              <ul className="scrape-list">
                {result.links.slice(0, 20).map((l, i) => (
                  <li key={i} className="scrape-link">{l}</li>
                ))}
              </ul>
            </div>
          )}

          {result.images.length > 0 && (
            <div className="scrape-section">
              <div className="scrape-section-title">Images ({result.images.length})</div>
              <ul className="scrape-list">
                {result.images.slice(0, 10).map((img, i) => (
                  <li key={i}>{img}</li>
                ))}
              </ul>
            </div>
          )}

          {Object.keys(result.meta).length > 0 && (
            <div className="scrape-section">
              <div className="scrape-section-title">Meta</div>
              {Object.entries(result.meta).map(([k, v]) => (
                <div key={k} className="score-detail">{k}: {v}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
