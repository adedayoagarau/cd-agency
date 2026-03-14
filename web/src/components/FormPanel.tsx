import { useState } from "react";
import { useStore } from "../store";
import { runAgent, scoreAll } from "../api";

export function FormPanel() {
  const {
    selectedAgent, setScores, addTokens, loading, setLoading, setError,
  } = useStore();
  const [content, setContent] = useState("");
  const [output, setOutput] = useState("");
  const [diff, setDiff] = useState<{ before: string; after: string } | null>(null);

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const charCount = content.length;

  const handleRun = async () => {
    if (!selectedAgent || !content.trim()) return;
    setLoading(true);
    setError("");
    try {
      const primaryInput = selectedAgent.slug.includes("error")
        ? "error_message"
        : "content";
      const res = await runAgent(selectedAgent.slug, { [primaryInput]: content });
      setOutput(res.content);
      setDiff({ before: content, after: res.content });
      addTokens(res.input_tokens + res.output_tokens);
    } catch (err: any) {
      setError(err.message);
      setOutput(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScore = async () => {
    if (!content.trim()) return;
    try {
      const s = await scoreAll(content);
      setScores(s);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAccept = () => {
    if (output) setContent(output);
  };

  // File System Access API
  const handleOpen = async () => {
    try {
      if ("showOpenFilePicker" in window) {
        const [handle] = await (window as any).showOpenFilePicker({
          types: [
            { description: "Text files", accept: { "text/*": [".txt", ".md", ".json", ".csv", ".yaml"] } },
          ],
        });
        const file = await handle.getFile();
        const text = await file.text();
        setContent(text);
      } else {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".txt,.md,.json,.csv,.yaml";
        input.onchange = async () => {
          const file = input.files?.[0];
          if (file) setContent(await file.text());
        };
        input.click();
      }
    } catch {
      // User cancelled
    }
  };

  const handleSave = async () => {
    const textToSave = output || content;
    if (!textToSave) return;
    try {
      if ("showSaveFilePicker" in window) {
        const handle = await (window as any).showSaveFilePicker({
          suggestedName: "content.md",
          types: [
            { description: "Markdown", accept: { "text/markdown": [".md"] } },
            { description: "Text", accept: { "text/plain": [".txt"] } },
          ],
        });
        const writable = await handle.createWritable();
        await writable.write(textToSave);
        await writable.close();
      } else {
        const blob = new Blob([textToSave], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "content.md";
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      // User cancelled
    }
  };

  return (
    <div className="panel form-panel">
      <div className="form-toolbar">
        <button className="btn btn-sm" onClick={handleOpen}>Open File</button>
        <button className="btn btn-sm" onClick={handleSave}>Save File</button>
        <span className="form-stats">Words: {wordCount} | Chars: {charCount}</span>
        <div className="form-toolbar-right">
          <button className="btn btn-sm" onClick={handleScore}>Score</button>
          <button
            className="btn btn-sm btn-primary"
            onClick={handleRun}
            disabled={!selectedAgent || !content.trim() || loading}
          >
            {loading ? "Running..." : "Run Agent"}
          </button>
        </div>
      </div>
      <div className="form-content">
        <div className="form-editor">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter or paste your content here..."
            className="editor-textarea"
          />
        </div>
        {output && (
          <div className="form-output">
            <div className="form-output-header">
              <span>Agent Output</span>
              <div>
                <button className="btn btn-sm btn-success" onClick={handleAccept}>Accept</button>
                <button className="btn btn-sm" onClick={() => navigator.clipboard.writeText(output)}>Copy</button>
              </div>
            </div>
            <div className="form-output-content">{output}</div>
            {diff && (
              <div className="form-diff">
                <div className="diff-before">- {diff.before}</div>
                <div className="diff-after">+ {diff.after}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
