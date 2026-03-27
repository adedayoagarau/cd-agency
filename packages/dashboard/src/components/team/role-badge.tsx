import { type MemberRole } from "@/lib/data/team";

const roleStyles: Record<MemberRole, string> = {
  owner: "bg-stone-800 text-white",
  admin: "bg-brand-100 text-brand-700",
  editor: "bg-blue-50 text-blue-700",
  viewer: "bg-stone-100 text-stone-600",
};

export function RoleBadge({ role }: { role: MemberRole }) {
  return (
    <span
      className={`text-xs font-medium px-2.5 py-0.5 rounded-full capitalize ${roleStyles[role]}`}
    >
      {role}
    </span>
  );
}
