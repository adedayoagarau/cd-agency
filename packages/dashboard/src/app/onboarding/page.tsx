"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { OnboardingProgress } from "@/components/onboarding/onboarding-progress";
import { StepWelcome } from "@/components/onboarding/step-welcome";
import { StepApiKey } from "@/components/onboarding/step-api-key";
import { StepFirstRun } from "@/components/onboarding/step-first-run";
import { StepOptional } from "@/components/onboarding/step-optional";

const TOTAL_STEPS = 4;

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const router = useRouter();

  function handleNext() {
    setStep((prev) => Math.min(prev + 1, TOTAL_STEPS));
  }

  function handleBack() {
    setStep((prev) => Math.max(prev - 1, 1));
  }

  function handleFinish() {
    localStorage.setItem("cd-agency-onboarding-complete", "true");
    router.push("/dashboard");
  }

  return (
    <>
      <OnboardingProgress currentStep={step} totalSteps={TOTAL_STEPS} />

      {step === 1 && <StepWelcome onNext={handleNext} />}
      {step === 2 && <StepApiKey onNext={handleNext} onBack={handleBack} />}
      {step === 3 && <StepFirstRun onNext={handleNext} onBack={handleBack} />}
      {step === 4 && <StepOptional onFinish={handleFinish} />}
    </>
  );
}
