"use client";

import { useState, useEffect } from "react";
import { CreditCard, Check, Minus, Key } from "lucide-react";
import { usageMeters, invoices } from "@/lib/data/billing";
import { UsageMeters } from "@/components/billing/usage-meters";
import { InvoiceTable } from "@/components/billing/invoice-table";
import { PlanSelector } from "@/components/billing/plan-selector";
import { getStoredKeys, type StoredKeys } from "@/lib/api-keys-store";

export default function BillingPage() {
  const [planSelectorOpen, setPlanSelectorOpen] = useState(false);
  const [keys, setKeys] = useState<StoredKeys>({});

  useEffect(() => {
    setKeys(getStoredKeys());
  }, []);

  const hasAnyKey = !!(keys.anthropic || keys.openai || keys.openrouter);
  const keyProviders = [
    { name: "Anthropic (Claude)", connected: !!keys.anthropic },
    { name: "OpenAI", connected: !!keys.openai },
    { name: "OpenRouter", connected: !!keys.openrouter },
  ];

  return (
    <div className="space-y-6">
      {/* Section 1: Current Plan */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="font-serif text-xl font-semibold text-stone-900">
                Pro
              </h2>
              <span className="bg-brand-50 text-brand-700 text-sm rounded-full px-3 py-0.5 font-medium">
                $29/month
              </span>
            </div>
            <p className="text-sm text-stone-500">
              500 agent runs &middot; 5 projects &middot; Brand DNA &middot;
              Connectors &middot; Email support
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPlanSelectorOpen(!planSelectorOpen)}
              className="text-brand-600 border border-brand-200 rounded-lg px-4 py-2 text-sm font-medium hover:bg-brand-50 transition-colors"
            >
              Change Plan
            </button>
          </div>
        </div>
        <div className="mt-3">
          <button className="text-xs text-stone-400 hover:text-rose-500 transition-colors">
            Cancel subscription
          </button>
        </div>
      </div>

      {/* Section 2: Usage This Period */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h3 className="text-base font-semibold text-stone-900 mb-4">
          Usage This Period
        </h3>
        <UsageMeters meters={usageMeters} />
      </div>

      {/* Section 3: BYOK */}
      <div className="bg-surface-highlight rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Key className="w-4 h-4 text-stone-500" />
          <h3 className="text-base font-semibold text-stone-900">
            Bring Your Own Keys
          </h3>
        </div>
        <div className="space-y-3 mb-4">
          {keyProviders.map((provider) => (
            <div
              key={provider.name}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                {provider.connected ? (
                  <Check className="w-4 h-4 text-emerald-500" />
                ) : (
                  <Minus className="w-4 h-4 text-stone-400" />
                )}
                <span className="text-sm text-stone-700">{provider.name}</span>
              </div>
              {provider.connected && (
                <span className="text-xs text-emerald-600 font-medium">
                  Connected
                </span>
              )}
            </div>
          ))}
        </div>
        <div className={`${hasAnyKey ? "bg-emerald-50" : "bg-stone-50"} rounded-lg p-3`}>
          <p className={`text-sm ${hasAnyKey ? "text-emerald-600" : "text-stone-500"}`}>
            {hasAnyKey
              ? "You're using your own API key — $0 platform cost."
              : "Add your own API keys in Settings to reduce platform costs."}
          </p>
        </div>
      </div>

      {/* Section 4: Payment Method */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-stone-400" />
            <div>
              <p className="text-sm font-medium text-stone-800">
                Visa ending in 4242
              </p>
              <p className="text-sm text-stone-500">Expires 12/2027</p>
            </div>
          </div>
          <button className="text-stone-600 border border-stone-200 rounded-lg px-4 py-2 text-sm font-medium hover:bg-stone-50 transition-colors">
            Update payment method
          </button>
        </div>
      </div>

      {/* Section 5: Invoices */}
      <div className="bg-surface-card rounded-xl p-6 shadow-soft">
        <h3 className="text-base font-semibold text-stone-900 mb-4">
          Invoices
        </h3>
        <InvoiceTable invoices={invoices} />
      </div>

      {/* Section 6: Plan Selector */}
      <PlanSelector
        open={planSelectorOpen}
        onClose={() => setPlanSelectorOpen(false)}
      />
    </div>
  );
}
