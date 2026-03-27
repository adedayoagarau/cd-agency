"use client";

import { useState } from "react";
import { BarChart3, Loader2, FileText, Shield, Eye, Zap } from "lucide-react";
import { useScoring } from "@/lib/hooks";

export default function ScoringPage() {
  const [text, setText] = useState("");
  const { score, result, loading, error } = useScoring();
  const [activeTab, setActiveTab] = useState<"readability" | "lint" | "a11y" | "all">("all");

  const handleScore = () => {
    if (!text.trim()) return;
    score(activeTab, text);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">Content Scoring</h1>
        <p className="text-stone-500 mt-1">Score your content for readability, quality, and accessibility — no API key required.</p>
      </div>

      {/* Input */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <label htmlFor="score-input" className="block text-sm font-medium text-stone-700 mb-2">
          Content to score
        </label>
        <textarea
          id="score-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your UI text, paragraph, or content here..."
          rows={5}
          className="w-full bg-white border border-stone-200 rounded-lg px-4 py-3 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
        />

        {/* Score type tabs */}
        <div className="flex items-center gap-2 mt-4">
          {[
            { key: "all" as const, label: "Score All", icon: Zap },
            { key: "readability" as const, label: "Readability", icon: FileText },
            { key: "lint" as const, label: "Linter", icon: Eye },
            { key: "a11y" as const, label: "Accessibility", icon: Shield },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === key
                  ? "bg-brand-500 text-white"
                  : "bg-stone-100 text-stone-600 hover:bg-stone-200"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}

          <button
            onClick={handleScore}
            disabled={loading || !text.trim()}
            className="ml-auto inline-flex items-center gap-1.5 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-5 py-1.5 rounded-lg text-sm font-medium transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
            {loading ? "Scoring..." : "Run Score"}
          </button>
        </div>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Readability card */}
          {(activeTab === "all" || activeTab === "readability") && (result as any).readability ? (
            <ReadabilityCard data={(result as any).readability} />
          ) : activeTab === "readability" ? (
            <ReadabilityCard data={result as any} />
          ) : null}

          {/* Linter card */}
          {(activeTab === "all" || activeTab === "lint") && (result as any).lint ? (
            <LintCard data={(result as any).lint} />
          ) : activeTab === "lint" ? (
            <LintCard data={result as any} />
          ) : null}

          {/* A11y card */}
          {(activeTab === "all" || activeTab === "a11y") && (result as any).a11y ? (
            <A11yCard data={(result as any).a11y} />
          ) : activeTab === "a11y" ? (
            <A11yCard data={result as any} />
          ) : null}
        </div>
      )}
    </div>
  );
}

function ReadabilityCard({ data }: { data: any }) {
  if (!data) return null;
  const ease = data.flesch_reading_ease ?? 0;
  const color = ease >= 60 ? "text-emerald-600" : ease >= 40 ? "text-amber-600" : "text-rose-600";
  const bg = ease >= 60 ? "bg-emerald-50" : ease >= 40 ? "bg-amber-50" : "bg-rose-50";

  return (
    <div className="bg-surface-card rounded-xl p-5 shadow-soft">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-4 h-4 text-stone-400" />
        <h3 className="text-sm font-semibold text-stone-900">Readability</h3>
      </div>
      <div className={`inline-flex items-center px-3 py-1.5 rounded-full ${bg} ${color} text-lg font-bold mb-3`}>
        {ease.toFixed(1)}
      </div>
      <p className="text-xs text-stone-500 mb-3">{data.ease_label || "Flesch Reading Ease"}</p>
      <div className="space-y-1.5 text-xs text-stone-600">
        <div className="flex justify-between"><span>Grade Level</span><span className="font-medium">{data.flesch_kincaid_grade?.toFixed(1)}</span></div>
        <div className="flex justify-between"><span>Words</span><span className="font-medium">{data.word_count}</span></div>
        <div className="flex justify-between"><span>Sentences</span><span className="font-medium">{data.sentence_count}</span></div>
        <div className="flex justify-between"><span>Avg Sentence Length</span><span className="font-medium">{data.avg_sentence_length?.toFixed(1)}</span></div>
        <div className="flex justify-between"><span>Reading Time</span><span className="font-medium">{data.reading_time_seconds?.toFixed(0)}s</span></div>
      </div>
    </div>
  );
}

function LintCard({ data }: { data: any }) {
  if (!data) return null;
  const issues = data.issues || [];
  const failed = issues.filter((i: any) => !i.passed);

  return (
    <div className="bg-surface-card rounded-xl p-5 shadow-soft">
      <div className="flex items-center gap-2 mb-4">
        <Eye className="w-4 h-4 text-stone-400" />
        <h3 className="text-sm font-semibold text-stone-900">Linter</h3>
      </div>
      <div className="flex items-center gap-3 mb-3">
        <span className="inline-flex items-center px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-600 text-sm font-bold">
          {data.passed_count ?? 0} passed
        </span>
        {(data.failed_count ?? failed.length) > 0 && (
          <span className="inline-flex items-center px-3 py-1.5 rounded-full bg-rose-50 text-rose-600 text-sm font-bold">
            {data.failed_count ?? failed.length} failed
          </span>
        )}
      </div>
      {failed.length > 0 && (
        <div className="space-y-2 mt-3">
          {failed.slice(0, 5).map((issue: any, i: number) => (
            <div key={i} className="text-xs p-2 rounded bg-rose-50 border border-rose-100">
              <p className="font-medium text-rose-800">{issue.message}</p>
              {issue.suggestion && <p className="text-rose-600 mt-0.5">{issue.suggestion}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function A11yCard({ data }: { data: any }) {
  if (!data) return null;
  const issues = data.issues || [];

  return (
    <div className="bg-surface-card rounded-xl p-5 shadow-soft">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-4 h-4 text-stone-400" />
        <h3 className="text-sm font-semibold text-stone-900">Accessibility</h3>
      </div>
      <div className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-bold mb-3 ${
        data.passed ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"
      }`}>
        {data.passed ? "Passed" : `${data.issue_count ?? issues.length} issues`}
      </div>
      <div className="space-y-1.5 text-xs text-stone-600 mb-3">
        <div className="flex justify-between"><span>Reading Grade</span><span className="font-medium">{data.reading_grade?.toFixed(1)}</span></div>
        <div className="flex justify-between"><span>Target Grade</span><span className="font-medium">{data.target_grade?.toFixed(1)}</span></div>
      </div>
      {issues.length > 0 && (
        <div className="space-y-2">
          {issues.slice(0, 5).map((issue: any, i: number) => (
            <div key={i} className="text-xs p-2 rounded bg-amber-50 border border-amber-100">
              <div className="flex items-center gap-1 mb-0.5">
                <span className="font-medium text-amber-800">[{issue.wcag_criterion}]</span>
                <span className="text-amber-700">{issue.severity}</span>
              </div>
              <p className="text-amber-800">{issue.message}</p>
              {issue.suggestion && <p className="text-amber-600 mt-0.5">{issue.suggestion}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
