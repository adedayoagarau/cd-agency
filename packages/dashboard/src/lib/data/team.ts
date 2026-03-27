export type MemberRole = "owner" | "admin" | "editor" | "viewer";

export interface TeamMember {
  name: string;
  email: string;
  role: MemberRole;
  initials: string;
  color: string;
  lastActive: string;
}

export const members: TeamMember[] = [
  { name: "Alex Lewis", email: "alex@acmecorp.com", role: "owner", initials: "AL", color: "brand", lastActive: "Now" },
  { name: "Sarah Jenkins", email: "sarah@acmecorp.com", role: "admin", initials: "SJ", color: "blue", lastActive: "14 min ago" },
  { name: "Marcus Reed", email: "marcus@acmecorp.com", role: "editor", initials: "MR", color: "purple", lastActive: "2 hours ago" },
  { name: "Lisa Chen", email: "lisa@acmecorp.com", role: "viewer", initials: "LC", color: "emerald", lastActive: "Yesterday" },
];

export const roleDescriptions: Record<MemberRole, string> = {
  owner: "Full access, billing, can delete workspace",
  admin: "Manage team, agents, connectors. Can't access billing.",
  editor: "Run agents, edit Brand DNA, use connectors",
  viewer: "Read-only access to outputs and history",
};
