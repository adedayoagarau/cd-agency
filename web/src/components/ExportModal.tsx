import { useState } from "react";
import { exportContent } from "../api";
import { useStore } from "../store";

interface Props {
  onClose: () => void;
}

const FORMATS = [
  { value: "json", label: "JSON", ext: ".json", mime: "application/json" },
  { value: "csv", label: "CSV", ext: ".csv", mime: "text/csv" },
  { value: "markdown", label: "Markdown", ext: ".md", mime: "text/markdown" },
  { value: "xliff", label: "XLIFF", ext: ".xliff", mime: "application/xml" },
];

export function ExportModal({ onClose }: Props) {
  const { setError } = useStore();
  const [format, setFormat] = useState("json");
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [entries, setEntries] = useState<{ source: string; target: string }[]>([]);
  const [exporting, setExporting] = useState(false);

  const addEntry = () => {
    if (!source.trim() || !target.trim()) return;
    setEntries([...entries, { source: source.trim(), target: target.trim() }]);
    setSource("");
    setTarget("");
  };

  const removeEntry = (i: number) => {
    setEntries(entries.filter((_, idx) => idx !== i));
  };

  const handleExport = async () => {
    if (entries.length === 0) return;
    setExporting(true);
    try {
      const text = await exportContent(entries, format);
      const fmt = FORMATS.find((f) => f.value === format)!;
      const blob = new Blob([text], { type: fmt.mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `export${fmt.ext}`;
      a.click();
      URL.revokeObjectURL(url);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Export Content</h3>
          <button className="btn btn-sm" onClick={onClose}>Close</button>
        </div>

        <div className="export-format-picker">
          <div className="sidebar-label">Format</div>
          <div className="export-formats">
            {FORMATS.map((f) => (
              <button
                key={f.value}
                className={`btn btn-sm ${format === f.value ? "btn-primary" : ""}`}
                onClick={() => setFormat(f.value)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="export-entry-form">
          <div className="sidebar-label">Add Entry</div>
          <textarea
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="Source text..."
            rows={2}
            className="editor-textarea"
          />
          <textarea
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Target text..."
            rows={2}
            className="editor-textarea"
          />
          <button className="btn btn-sm" onClick={addEntry} disabled={!source.trim() || !target.trim()}>
            Add Entry
          </button>
        </div>

        {entries.length > 0 && (
          <div className="export-entries">
            <div className="sidebar-label">Entries ({entries.length})</div>
            {entries.map((e, i) => (
              <div key={i} className="export-entry-item">
                <div className="export-entry-preview">
                  <span className="diff-before">{e.source.slice(0, 60)}</span>
                  <span className="diff-after">{e.target.slice(0, 60)}</span>
                </div>
                <button className="btn btn-sm" onClick={() => removeEntry(i)}>Remove</button>
              </div>
            ))}
          </div>
        )}

        <div className="modal-footer">
          <button
            className="btn btn-primary"
            onClick={handleExport}
            disabled={entries.length === 0 || exporting}
          >
            {exporting ? "Exporting..." : `Export ${entries.length} entries as ${format.toUpperCase()}`}
          </button>
        </div>
      </div>
    </div>
  );
}
