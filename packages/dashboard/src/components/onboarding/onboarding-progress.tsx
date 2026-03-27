"use client";

interface OnboardingProgressProps {
  currentStep: number;
  totalSteps: number;
}

export function OnboardingProgress({ currentStep, totalSteps }: OnboardingProgressProps) {
  return (
    <div className="flex items-center justify-center mb-8 gap-2">
      {Array.from({ length: totalSteps }, (_, i) => {
        const step = i + 1;
        const isActive = step === currentStep;
        const isCompleted = step < currentStep;

        return (
          <div
            key={step}
            className={[
              "h-2 rounded-full transition-all duration-300",
              isActive
                ? "w-8 bg-brand-500"
                : isCompleted
                  ? "w-2 bg-brand-500"
                  : "w-2 bg-stone-200",
            ].join(" ")}
          />
        );
      })}
    </div>
  );
}
