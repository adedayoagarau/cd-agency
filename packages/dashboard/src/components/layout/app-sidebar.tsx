"use client";

import Link from "next/link";
import {
  LayoutDashboard,
  Bot,
  Dna,
  Brain,
  Plug,
  Clock,
  BarChart3,
  CheckCircle,
  GitBranch,
  Palette,
  Globe,
  Users,
  CreditCard,
  Key,
  Settings,
  BookOpen,
  MessageCircle,
} from "lucide-react";
import { SidebarNavItem } from "./sidebar-nav-item";

const workspaceNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/brand-dna", label: "Brand DNA", icon: Dna },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/connectors", label: "Connectors", icon: Plug },
  { href: "/history", label: "History", icon: Clock },
];

const toolsNav = [
  { href: "/scoring", label: "Scoring", icon: BarChart3 },
  { href: "/validate", label: "Validation", icon: CheckCircle },
  { href: "/workflows", label: "Workflows", icon: GitBranch },
  { href: "/presets", label: "Presets", icon: Palette },
  { href: "/scrape", label: "Scrape", icon: Globe },
];

const settingsNav = [
  { href: "/team", label: "Team", icon: Users },
  { href: "/billing", label: "Billing", icon: CreditCard },
  { href: "/api-keys", label: "API Keys", icon: Key },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppSidebar() {
  return (
    <aside
      className="hidden md:flex w-[240px] flex-shrink-0 bg-surface-sidebar flex-col justify-between border-r border-stone-200/50"
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Top section */}
      <div className="flex flex-col overflow-y-auto">
        {/* Logo */}
        <div className="h-16 border-b border-stone-200/50 flex items-center px-6">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded bg-brand-500 flex items-center justify-center">
              <span className="text-white font-serif text-xs font-bold leading-none">cd</span>
            </div>
            <span className="font-serif font-semibold text-lg text-stone-900">cd-agency</span>
          </Link>
        </div>

        {/* Workspace nav */}
        <div className="px-3 pt-6">
          <p className="px-3 pb-2 text-[11px] uppercase tracking-wider text-stone-400 font-medium">
            Workspace
          </p>
          <nav className="flex flex-col gap-0.5">
            {workspaceNav.map((item) => (
              <SidebarNavItem key={item.href} {...item} />
            ))}
          </nav>
        </div>

        {/* Tools nav */}
        <div className="px-3 pt-6">
          <p className="px-3 pb-2 text-[11px] uppercase tracking-wider text-stone-400 font-medium">
            Tools
          </p>
          <nav className="flex flex-col gap-0.5">
            {toolsNav.map((item) => (
              <SidebarNavItem key={item.href} {...item} />
            ))}
          </nav>
        </div>

        {/* Settings nav */}
        <div className="px-3 pt-6">
          <p className="px-3 pb-2 text-[11px] uppercase tracking-wider text-stone-400 font-medium">
            Settings
          </p>
          <nav className="flex flex-col gap-0.5">
            {settingsNav.map((item) => (
              <SidebarNavItem key={item.href} {...item} />
            ))}
          </nav>
        </div>
      </div>

      {/* Bottom section */}
      <div className="border-t border-stone-200/50 p-3 flex flex-col gap-0.5">
        <Link
          href="/docs"
          className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-200/30 hover:text-stone-900 rounded-md transition-colors"
        >
          <BookOpen size={16} className="opacity-70" aria-hidden="true" />
          Documentation
        </Link>
        <Link
          href="/feedback"
          className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-200/30 hover:text-stone-900 rounded-md transition-colors"
        >
          <MessageCircle size={16} className="opacity-70" aria-hidden="true" />
          Feedback
        </Link>

        {/* Profile */}
        <button className="flex items-center gap-3 px-3 py-2 mt-1 rounded-md hover:bg-stone-200/30 transition-colors w-full text-left">
          <div className="w-7 h-7 rounded-full bg-brand-100 border border-brand-200 flex items-center justify-center">
            <span className="text-brand-700 text-xs font-semibold">AL</span>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-medium text-stone-900 truncate">Alex Lewis</span>
            <span className="text-xs text-stone-500 truncate">alex@acmecorp.com</span>
          </div>
        </button>
      </div>
    </aside>
  );
}
