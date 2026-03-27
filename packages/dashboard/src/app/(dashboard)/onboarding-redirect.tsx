"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function OnboardingRedirect() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const completed = localStorage.getItem("cd-agency-onboarding-complete");
      if (!completed) {
        router.replace("/onboarding");
      }
    }
  }, [router]);

  return null;
}
