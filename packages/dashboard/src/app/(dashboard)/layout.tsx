import { AppSidebar } from "@/components/layout/app-sidebar";
import { Topbar } from "@/components/layout/topbar";
import { MobileNav } from "@/components/layout/mobile-nav";
import { OnboardingRedirect } from "./onboarding-redirect";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen w-screen overflow-hidden flex">
      <OnboardingRedirect />
      <AppSidebar />
      <main className="flex-1 flex flex-col min-w-0 relative">
        <Topbar />
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-[1100px] mx-auto pb-12">
            {children}
          </div>
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
