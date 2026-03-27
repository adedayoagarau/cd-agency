import { Check } from "lucide-react";
import { type Plan } from "@/lib/data/billing";

export function PlanCard({
  plan,
  onSelect,
}: {
  plan: Plan;
  onSelect: (planId: string) => void;
}) {
  const isCheaper =
    !plan.isCurrent &&
    (plan.id === "free");
  const isEnterprise = plan.id === "enterprise";

  let buttonLabel = "Upgrade";
  let buttonClass =
    "bg-brand-500 text-white hover:bg-brand-600";

  if (plan.isCurrent) {
    buttonLabel = "Current Plan";
    buttonClass = "bg-stone-100 text-stone-400 cursor-not-allowed";
  } else if (isCheaper) {
    buttonLabel = "Downgrade";
    buttonClass =
      "text-stone-600 border border-stone-200 hover:bg-stone-50";
  } else if (isEnterprise) {
    buttonLabel = "Contact Sales";
    buttonClass =
      "text-stone-600 border border-stone-200 hover:bg-stone-50";
  }

  return (
    <div
      className={`bg-white rounded-xl p-6 border-2 transition-colors relative ${
        plan.isCurrent
          ? "border-brand-500 ring-1 ring-brand-200"
          : "border-stone-200 hover:border-brand-200"
      }`}
    >
      {/* Popular badge */}
      {plan.isPopular && (
        <span className="absolute -top-2.5 left-4 bg-brand-500 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded-full">
          Popular
        </span>
      )}

      {/* Plan name */}
      <h3 className="font-serif text-lg font-semibold text-stone-900 mt-1">
        {plan.name}
      </h3>

      {/* Price */}
      <div className="mt-3 mb-5">
        <span className="text-3xl font-bold text-stone-900">{plan.price}</span>
        {plan.period && (
          <span className="text-sm text-stone-400">{plan.period}</span>
        )}
      </div>

      {/* Features */}
      <ul className="space-y-2 mb-6">
        {plan.features.map((feature) => (
          <li key={feature} className="flex items-start gap-2">
            <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
            <span className="text-sm text-stone-600">{feature}</span>
          </li>
        ))}
      </ul>

      {/* Button */}
      <button
        onClick={() => onSelect(plan.id)}
        disabled={plan.isCurrent}
        className={`w-full py-2.5 rounded-lg text-sm font-medium transition-colors ${buttonClass}`}
      >
        {buttonLabel}
      </button>
    </div>
  );
}
