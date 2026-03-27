"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, ChevronDown } from "lucide-react";
import { Command } from "cmdk";

export function Topbar() {
  const [open, setOpen] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    },
    []
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <>
      <header className="hidden md:flex glass-topbar h-16 border-b border-stone-200/60 items-center justify-between px-8 z-10 sticky top-0">
        {/* Left: Command palette trigger */}
        <button
          onClick={() => setOpen(true)}
          className="w-64 flex items-center gap-2 bg-stone-100 hover:bg-stone-200 border border-stone-200 rounded-md px-3 py-1.5 text-sm text-stone-500 transition-colors"
        >
          <Search size={14} aria-hidden="true" />
          <span className="flex-1 text-left truncate">Search workspaces, agents...</span>
          <div className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 text-[11px] font-medium bg-white border border-stone-300 rounded text-stone-500">
              ⌘
            </kbd>
            <kbd className="px-1.5 py-0.5 text-[11px] font-medium bg-white border border-stone-300 rounded text-stone-500">
              K
            </kbd>
          </div>
        </button>

        {/* Right: Org switcher + avatar */}
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 hover:bg-stone-100 rounded-md px-2 py-1.5 transition-colors">
            <div className="w-5 h-5 rounded bg-stone-800 flex items-center justify-center">
              <span className="text-white text-[10px] font-bold">A</span>
            </div>
            <span className="text-sm font-medium text-stone-700">Acme Corp</span>
            <ChevronDown size={14} className="text-stone-400" aria-hidden="true" />
          </button>

          <div className="w-px h-6 bg-stone-200" />

          <button className="w-8 h-8 rounded-full border border-stone-200 hover:ring-2 ring-brand-200 overflow-hidden transition-all">
            <div className="w-full h-full bg-brand-100 flex items-center justify-center">
              <span className="text-brand-700 text-xs font-semibold">AL</span>
            </div>
          </button>
        </div>
      </header>

      {/* Command Palette Dialog */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />

          {/* Command palette */}
          <div className="relative w-full max-w-lg bg-white rounded-xl shadow-2xl border border-stone-200 overflow-hidden">
            <Command className="flex flex-col">
              <Command.Input
                placeholder="Search workspaces, agents, actions..."
                className="w-full px-4 py-3 text-sm border-b border-stone-200 outline-none placeholder:text-stone-400"
                autoFocus
              />
              <Command.List className="max-h-80 overflow-y-auto p-2">
                <Command.Empty className="py-6 text-center text-sm text-stone-500">
                  No results found.
                </Command.Empty>

                <Command.Group
                  heading="Agents"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-stone-400"
                >
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Error Messages
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Microcopy
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Onboarding Flow
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Empty States
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Notifications
                  </Command.Item>
                </Command.Group>

                <Command.Group
                  heading="Navigation"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-stone-400"
                >
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Dashboard
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Agents
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Brand DNA
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Memory
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Settings
                  </Command.Item>
                </Command.Group>

                <Command.Group
                  heading="Actions"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-stone-400"
                >
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Quick Run
                  </Command.Item>
                  <Command.Item
                    className="flex items-center gap-2 px-2 py-2 text-sm text-stone-700 rounded-md cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    onSelect={() => setOpen(false)}
                  >
                    Sync Connectors
                  </Command.Item>
                </Command.Group>
              </Command.List>
            </Command>
          </div>
        </div>
      )}
    </>
  );
}
