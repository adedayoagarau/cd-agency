"use client";

import { useState } from "react";
import { X } from "lucide-react";

type InviteRole = "admin" | "editor" | "viewer";

const roleOptions: { value: InviteRole; label: string }[] = [
  { value: "admin", label: "Admin" },
  { value: "editor", label: "Editor" },
  { value: "viewer", label: "Viewer" },
];

export function InviteDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [selectedRole, setSelectedRole] = useState<InviteRole>("editor");
  const [emails, setEmails] = useState("");

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-6 shadow-2xl w-full max-w-md relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-stone-400 hover:text-stone-600 transition-colors"
          aria-label="Close dialog"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <h2 className="font-serif text-xl font-semibold text-stone-900 mb-5">
          Invite team members
        </h2>

        {/* Email input */}
        <div className="mb-5">
          <label
            htmlFor="invite-emails"
            className="block text-sm font-medium text-stone-700 mb-1.5"
          >
            Email addresses
          </label>
          <input
            id="invite-emails"
            type="text"
            value={emails}
            onChange={(e) => setEmails(e.target.value)}
            placeholder="Enter emails, separated by commas"
            className="w-full border border-stone-200 rounded-lg px-3 py-2.5 text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand-300 focus:border-brand-400"
          />
        </div>

        {/* Role selector */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-stone-700 mb-2">
            Role
          </label>
          <div className="grid grid-cols-3 gap-2">
            {roleOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setSelectedRole(opt.value)}
                className={`border rounded-lg p-3 text-sm font-medium transition-colors ${
                  selectedRole === opt.value
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-stone-200 text-stone-600 hover:border-stone-300"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Send button */}
        <button
          className="bg-brand-500 text-white w-full py-2.5 rounded-lg text-sm font-medium mt-4 hover:bg-brand-600 transition-colors"
          onClick={onClose}
        >
          Send Invite
        </button>
      </div>
    </div>
  );
}
