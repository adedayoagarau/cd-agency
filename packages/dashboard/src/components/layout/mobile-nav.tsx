"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bot, ArrowUp, Dna, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/brand-dna", label: "Brand", icon: Dna },
  { href: "/settings", label: "More", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 h-16 bg-white border-t border-stone-200 z-50 flex md:hidden items-center justify-around px-2">
      {/* Home */}
      <Link
        href="/dashboard"
        className={cn(
          "flex flex-col items-center gap-0.5",
          pathname === "/dashboard" ? "text-brand-600" : "text-stone-500"
        )}
      >
        <LayoutDashboard size={20} aria-hidden="true" />
        <span className="text-[10px] font-medium">Home</span>
      </Link>

      {/* Agents */}
      <Link
        href="/agents"
        className={cn(
          "flex flex-col items-center gap-0.5",
          pathname === "/agents" ? "text-brand-600" : "text-stone-500"
        )}
      >
        <Bot size={20} aria-hidden="true" />
        <span className="text-[10px] font-medium">Agents</span>
      </Link>

      {/* Run (elevated) */}
      <Link
        href="/run"
        className="flex flex-col items-center gap-0.5"
      >
        <div className="w-10 h-10 -mt-5 rounded-full bg-brand-500 text-white shadow-lg flex items-center justify-center">
          <ArrowUp size={20} aria-hidden="true" />
        </div>
        <span className="text-[10px] font-medium text-stone-500">Run</span>
      </Link>

      {/* Brand */}
      <Link
        href="/brand-dna"
        className={cn(
          "flex flex-col items-center gap-0.5",
          pathname === "/brand-dna" ? "text-brand-600" : "text-stone-500"
        )}
      >
        <Dna size={20} aria-hidden="true" />
        <span className="text-[10px] font-medium">Brand</span>
      </Link>

      {/* More */}
      <Link
        href="/settings"
        className={cn(
          "flex flex-col items-center gap-0.5",
          pathname === "/settings" ? "text-brand-600" : "text-stone-500"
        )}
      >
        <Settings size={20} aria-hidden="true" />
        <span className="text-[10px] font-medium">More</span>
      </Link>
    </nav>
  );
}
