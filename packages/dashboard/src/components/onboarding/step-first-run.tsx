"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";

interface StepFirstRunProps {
  onNext: () => void;
  onBack: () => void;
}

export function StepFirstRun({ onNext, onBack }: StepFirstRunProps) {
  const [running, setRunning] = useState(false);
  const [showOutput, setShowOutput] = useState(false);

  function handleRun() {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
      setShowOutput(true);
    }, 1500);
  }

  return (
    <div className="flex flex-col">
      <h1 className="font-serif text-2xl text-center text-stone-900">
        Let&apos;s run your first agent
      </h1>

      {/* Agent card */}
      <div className="bg-surface-card rounded-xl p-4 mb-4 mt-6 border border-stone-200">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-stone-900">Microcopy Writer</span>
          <span className="bg-blue-50 text-blue-700 text-[10px] rounded-full px-2 py-0.5 font-medium">
            Writing
          </span>
        </div>
      </div>

      {/* Pre-filled input */}
      <div className="bg-stone-50 rounded-lg p-3 text-sm text-stone-700 mb-4">
        Write a button label for uploading a profile photo
      </div>

      {/* Run button */}
      {!showOutput && (
        <button
          onClick={handleRun}
          disabled={running}
          className="bg-brand-500 text-white w-full h-11 rounded-xl text-sm font-medium hover:bg-brand-600 transition-colors disabled:opacity-70 flex items-center justify-center gap-2"
        >
          <Sparkles size={16} />
          {running ? "Running..." : "Run Agent"}
        </button>
      )}

      {/* Output area */}
      <div
        className={[
          "transition-all duration-500",
          showOutput ? "opacity-100 max-h-96" : "opacity-0 max-h-0 overflow-hidden",
        ].join(" ")}
      >
        <div className="bg-surface-card rounded-xl p-4 border border-stone-200">
          <p className="text-base font-medium text-stone-800">Choose your photo</p>

          {/* Mini evaluation */}
          <div className="flex items-center gap-3 mt-3">
            <span className="text-emerald-600 font-semibold text-sm">Score 91%</span>
            <div className="flex items-center gap-1">
              <div className="w-6 h-1.5 rounded-full bg-emerald-500" />
              <div className="w-6 h-1.5 rounded-full bg-emerald-500" />
              <div className="w-6 h-1.5 rounded-full bg-emerald-500" />
              <div className="w-6 h-1.5 rounded-full bg-stone-200" />
            </div>
          </div>

          <p className="text-sm text-brand-600 font-medium mt-3">
            Your first AI-assisted content!
          </p>
        </div>

        {/* Continue to dashboard */}
        <button
          onClick={onNext}
          className="bg-brand-500 text-white w-full h-11 rounded-xl mt-4 text-sm font-medium hover:bg-brand-600 transition-colors"
        >
          Continue to dashboard
        </button>
      </div>

      {/* Back */}
      <button
        onClick={onBack}
        className="text-sm text-stone-400 hover:text-stone-600 text-center mt-3 transition-colors"
      >
        Back
      </button>
    </div>
  );
}
