"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function OnboardingRedirect() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const completed = localStorage.getItem("cd-agency-onboarding-complete");
      if (!completed) {
        // Show onboarding banner instead of hard redirect
        setChecked(true);
      } else {
        setChecked(true);
      }
    }
  }, [router]);

  if (!checked) return null;

  const completed = typeof window !== "undefined"
    ? localStorage.getItem("cd-agency-onboarding-complete")
    : null;

  if (completed) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-brand-500 text-white text-sm text-center py-2 px-4">
      New here?{" "}
      <a href="/onboarding" className="underline font-medium">
        Complete the setup guide
      </a>{" "}
      or{" "}
      <button
        onClick={() => {
          localStorage.setItem("cd-agency-onboarding-complete", "true");
          window.location.reload();
        }}
        className="underline font-medium"
      >
        dismiss
      </button>
    </div>
  );
}
