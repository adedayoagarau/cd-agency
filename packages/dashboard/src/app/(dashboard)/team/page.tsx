"use client";

import { useState } from "react";
import { UserPlus, Link2, Check } from "lucide-react";
import { members, roleDescriptions, type MemberRole } from "@/lib/data/team";
import { MemberRow } from "@/components/team/member-row";
import { InviteDialog } from "@/components/team/invite-dialog";

const roleOrder: MemberRole[] = ["owner", "admin", "editor", "viewer"];

export default function TeamPage() {
  const [inviteOpen, setInviteOpen] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  const handleCopyInviteLink = () => {
    const inviteUrl = `${window.location.origin}/invite?team=acme-corp&ref=dashboard`;
    navigator.clipboard.writeText(inviteUrl);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="font-serif text-2xl font-semibold text-stone-900">
            Team
          </h1>
          <span className="bg-stone-100 text-stone-600 text-xs rounded-full px-2.5 py-0.5 font-medium">
            {members.length} members
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyInviteLink}
            className="text-stone-600 border border-stone-200 text-sm px-4 py-2 rounded-lg font-medium hover:bg-stone-50 transition-colors inline-flex items-center gap-2"
          >
            {linkCopied ? (
              <>
                <Check className="w-4 h-4 text-emerald-500" />
                Copied!
              </>
            ) : (
              <>
                <Link2 className="w-4 h-4" />
                Copy Invite Link
              </>
            )}
          </button>
          <button
            onClick={() => setInviteOpen(true)}
            className="bg-brand-500 text-white text-sm px-4 py-2 rounded-lg font-medium hover:bg-brand-600 transition-colors inline-flex items-center gap-2"
          >
            <UserPlus className="w-4 h-4" />
            Invite member
          </button>
        </div>
      </div>

      {/* Toast notification */}
      {linkCopied && (
        <div className="fixed bottom-6 right-6 bg-stone-900 text-white text-sm px-4 py-3 rounded-lg shadow-lg z-50 animate-in slide-in-from-bottom-2">
          Invite link copied — team features coming soon.
        </div>
      )}

      {/* Roles explanation card */}
      <div className="bg-surface-highlight rounded-xl p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {roleOrder.map((role) => (
            <div key={role} className="flex flex-col gap-0.5">
              <span className="font-medium text-sm text-stone-800 capitalize">
                {role}
              </span>
              <span className="text-xs text-stone-500">
                {roleDescriptions[role]}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Member list */}
      <div className="bg-surface-card rounded-xl shadow-soft divide-y divide-stone-100 overflow-hidden">
        {members.map((member, idx) => (
          <MemberRow
            key={member.email}
            member={member}
            isCurrentUser={idx === 0}
          />
        ))}
      </div>

      {/* Invite dialog */}
      <InviteDialog open={inviteOpen} onClose={() => setInviteOpen(false)} />
    </div>
  );
}
