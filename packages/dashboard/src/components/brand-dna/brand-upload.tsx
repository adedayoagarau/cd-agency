"use client";

import { useRef, useState } from "react";
import { Upload, FileText } from "lucide-react";

interface BrandUploadProps {
  onIngest?: (content: string) => Promise<void>;
}

export function BrandUpload({ onIngest }: BrandUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showPaste, setShowPaste] = useState(false);
  const [pastedText, setPastedText] = useState("");
  const [processing, setProcessing] = useState(false);

  async function handleFile(file: File) {
    if (!onIngest) return;
    setProcessing(true);
    try {
      const text = await file.text();
      await onIngest(text);
    } finally {
      setProcessing(false);
    }
  }

  async function handlePaste() {
    if (!onIngest || !pastedText.trim()) return;
    setProcessing(true);
    try {
      await onIngest(pastedText.trim());
      setPastedText("");
      setShowPaste(false);
    } finally {
      setProcessing(false);
    }
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setShowPaste((v) => !v)}
          className="border border-stone-200 text-stone-600 px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:bg-stone-50 transition-colors"
        >
          <FileText className="w-4 h-4" />
          Paste
        </button>
        <button
          type="button"
          disabled={processing}
          onClick={() => fileInputRef.current?.click()}
          className="bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:bg-brand-600 transition-colors disabled:opacity-50"
        >
          <Upload className="w-4 h-4" />
          {processing ? "Processing..." : "Upload"}
        </button>
      </div>

      {showPaste && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 w-full max-w-lg mx-4">
            <h3 className="text-base font-semibold text-stone-900 mb-3">
              Paste brand content
            </h3>
            <textarea
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste your brand guidelines, style guide, or any brand content here..."
              className="w-full h-48 border border-stone-200 rounded-lg px-3 py-2 text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-200 focus:border-brand-300 resize-none"
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                type="button"
                onClick={() => {
                  setShowPaste(false);
                  setPastedText("");
                }}
                className="px-4 py-2 text-sm font-medium text-stone-600 hover:text-stone-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={processing || !pastedText.trim()}
                onClick={handlePaste}
                className="bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-50"
              >
                {processing ? "Processing..." : "Process"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
