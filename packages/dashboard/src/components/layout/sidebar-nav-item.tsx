"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { type LucideIcon } from "lucide-react";

interface SidebarNavItemProps {
  href: string;
  label: string;
  icon: LucideIcon;
}

export function SidebarNavItem({ href, label, icon: Icon }: SidebarNavItemProps) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
        isActive
          ? "bg-brand-50 text-brand-700 border-l-2 border-brand-500"
          : "text-stone-600 hover:bg-stone-200/30 hover:text-stone-900"
      )}
    >
      <Icon size={16} className={cn(!isActive && "opacity-70")} aria-hidden="true" />
      {label}
    </Link>
  );
}
