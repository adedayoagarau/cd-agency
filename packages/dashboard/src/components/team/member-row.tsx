import { Trash2 } from "lucide-react";
import { type TeamMember, type MemberRole } from "@/lib/data/team";
import { RoleBadge } from "./role-badge";

const avatarColors: Record<string, string> = {
  brand: "bg-brand-100 text-brand-700",
  blue: "bg-blue-100 text-blue-700",
  purple: "bg-purple-100 text-purple-700",
  emerald: "bg-emerald-100 text-emerald-700",
};

const roles: MemberRole[] = ["owner", "admin", "editor", "viewer"];

export function MemberRow({
  member,
  isCurrentUser,
}: {
  member: TeamMember;
  isCurrentUser: boolean;
}) {
  return (
    <div className="flex items-center p-4 gap-4">
      {/* Avatar */}
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold ${avatarColors[member.color] ?? avatarColors.brand}`}
      >
        {member.initials}
      </div>

      {/* Name + Email */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-stone-800 truncate">
          {member.name}
          {isCurrentUser && (
            <span className="text-stone-400"> (you)</span>
          )}
        </p>
        <p className="text-xs text-stone-400 truncate">{member.email}</p>
      </div>

      {/* Role selector */}
      <div className="hidden sm:block">
        {member.role === "owner" ? (
          <RoleBadge role={member.role} />
        ) : (
          <select
            defaultValue={member.role}
            className="bg-white border border-stone-200 rounded-lg px-2 py-1 text-xs text-stone-700 focus:outline-none focus:ring-1 focus:ring-brand-300"
          >
            {roles.map((r) => (
              <option key={r} value={r}>
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Last active */}
      <span className="text-xs text-stone-400 w-24 text-right hidden md:block">
        {member.lastActive}
      </span>

      {/* Remove button */}
      {isCurrentUser ? (
        <div className="w-8 h-8" />
      ) : (
        <button
          className="w-8 h-8 rounded-lg flex items-center justify-center text-stone-300 hover:text-rose-600 hover:bg-rose-50 transition-colors"
          aria-label={`Remove ${member.name}`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
