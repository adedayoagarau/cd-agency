"use client";

import { useState } from "react";
import { CheckCircle, XCircle, Loader2, AlertTriangle } from "lucide-react";
import { useElementTypes, useValidate } from "@/lib/hooks";

export default function ValidatePage() {
  const [text, setText] = useState("");
  const [elementType, setElementType] = useState("button");
  const [platform, setPlatform] = useState("");
  const { data: elementTypes } = useElementTypes();
  const { validate, result, loading, error } = useValidate();

  const handleValidate = () => {
    if (!text.trim()) return;
    validate(text, elementType, platform || undefined);
  };

  const validationResult = result as any;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">Content Validation</h1>
        <p className="text-stone-500 mt-1">Check content against UI constraints — character limits, platform rules, accessibility.</p>
      </div>

      {/* Input */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-stone-500 mb-1.5">Element Type</label>
            <select
              value={elementType}
              onChange={(e) => setElementType(e.target.value)}
              className="w-full bg-white border border-stone-200 rounded-lg px-4 py-2.5 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              {elementTypes ? elementTypes.map((et) => (
                <option key={et.type} value={et.type}>
                  {et.label} ({et.max_chars} chars)
                </option>
              )) : (
                <>
                  <option value="button">Button</option>
                  <option value="tooltip">Tooltip</option>
                  <option value="heading">Heading</option>
                  <option value="error">Error Message</option>
                  <option value="notification">Notification</option>
                </>
              )}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-stone-500 mb-1.5">Platform (optional)</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full bg-white border border-stone-200 rounded-lg px-4 py-2.5 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="">Any</option>
              <option value="ios">iOS</option>
              <option value="android">Android</option>
              <option value="web">Web</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleValidate}
              disabled={loading || !text.trim()}
              className="w-full inline-flex items-center justify-center gap-1.5 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              {loading ? "Validating..." : "Validate"}
            </button>
          </div>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter the UI text to validate..."
          rows={3}
          className="w-full bg-white border border-stone-200 rounded-lg px-4 py-3 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        />

        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-stone-400">{text.length} characters</span>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      </div>

      {/* Results */}
      {validationResult && (
        <div className="bg-surface-card rounded-xl p-6 shadow-soft">
          <div className="flex items-center gap-3 mb-4">
            {validationResult.passed ? (
              <div className="flex items-center gap-2 text-emerald-600">
                <CheckCircle className="w-5 h-5" />
                <span className="text-lg font-semibold">Passed</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-rose-600">
                <XCircle className="w-5 h-5" />
                <span className="text-lg font-semibold">
                  {validationResult.error_count} error{validationResult.error_count !== 1 ? "s" : ""}, {validationResult.warning_count} warning{validationResult.warning_count !== 1 ? "s" : ""}
                </span>
              </div>
            )}
          </div>

          {validationResult.summary && (
            <p className="text-sm text-stone-600 mb-4">{validationResult.summary}</p>
          )}

          {validationResult.violations?.length > 0 && (
            <div className="space-y-2">
              {validationResult.violations.map((v: any, i: number) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    v.severity === "error"
                      ? "bg-rose-50 border-rose-200"
                      : "bg-amber-50 border-amber-200"
                  }`}
                >
                  {v.severity === "error" ? (
                    <XCircle className="w-4 h-4 text-rose-500 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                  )}
                  <div>
                    <p className={`text-sm font-medium ${
                      v.severity === "error" ? "text-rose-800" : "text-amber-800"
                    }`}>
                      {v.rule}: {v.message}
                    </p>
                    {v.value && v.limit && (
                      <p className="text-xs text-stone-500 mt-0.5">
                        Value: {v.value} / Limit: {v.limit}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
