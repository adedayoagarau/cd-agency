"use client";

import { plans } from "@/lib/data/billing";
import { PlanCard } from "./plan-card";

export function PlanSelector({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  if (!open) return null;

  return (
    <div className="bg-surface-card rounded-xl p-6 shadow-soft">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-serif text-lg font-semibold text-stone-900">
          Choose a Plan
        </h3>
        <button
          onClick={onClose}
          className="text-sm text-stone-400 hover:text-stone-600 transition-colors"
        >
          Close
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {plans.map((plan) => (
          <PlanCard key={plan.id} plan={plan} onSelect={() => onClose()} />
        ))}
      </div>
    </div>
  );
}
