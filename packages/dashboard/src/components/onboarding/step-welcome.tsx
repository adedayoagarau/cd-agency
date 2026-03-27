"use client";

import { useState } from "react";

interface StepWelcomeProps {
  onNext: () => void;
}

export function StepWelcome({ onNext }: StepWelcomeProps) {
  const [showInput, setShowInput] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");

  function handleClick() {
    if (!showInput) {
      setShowInput(true);
      return;
    }
    if (workspaceName.trim()) {
      onNext();
    }
  }

  return (
    <div className="flex flex-col items-center">
      {/* Logo */}
      <div className="w-16 h-16 mx-auto mb-6 bg-brand-500 rounded-2xl flex items-center justify-center">
        <span className="text-white font-serif text-2xl font-bold">cd</span>
      </div>

      <h1 className="font-serif text-3xl text-center text-stone-900">
        Welcome to cd-agency
      </h1>
      <p className="text-stone-500 text-center mt-2 mb-8">
        AI-powered content design for teams who care about every word.
      </p>

      {/* Workspace name input */}
      <div
        className={[
          "w-full overflow-hidden transition-all duration-300",
          showInput ? "max-h-40 opacity-100 mb-4" : "max-h-0 opacity-0",
        ].join(" ")}
      >
        <label
          htmlFor="workspace-name"
          className="block text-sm font-medium text-stone-700 mb-1.5"
        >
          Workspace name
        </label>
        <input
          id="workspace-name"
          type="text"
          value={workspaceName}
          onChange={(e) => setWorkspaceName(e.target.value)}
          placeholder="e.g. Acme Corp"
          className="w-full h-11 rounded-lg border border-stone-200 bg-white px-3 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-colors"
        />
      </div>

      <button
        onClick={handleClick}
        disabled={showInput && !workspaceName.trim()}
        className="bg-brand-500 text-white w-full h-12 rounded-xl text-base font-medium hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {showInput && workspaceName.trim() ? "Continue" : "Create your workspace"}
      </button>
    </div>
  );
}
