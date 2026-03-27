import { Link } from "lucide-react";

interface ActivityItem {
  user: string | null;
  avatar?: "img";
  initials?: string;
  color?: "blue" | "purple";
  isSystem?: boolean;
  action: string;
  target: string | null;
  time: string;
}

const activities: ActivityItem[] = [
  { user: "You", avatar: "img", action: "updated", target: "Brand Rules", time: "2m ago" },
  {
    user: "Sarah Jenkins",
    initials: "SJ",
    color: "blue",
    action: "ran",
    target: "Microcopy Writer",
    time: "14m ago",
  },
  {
    user: "Marcus Reed",
    initials: "MR",
    color: "purple",
    action: "added a new term to",
    target: "Terminology",
    time: "2h ago",
  },
  {
    user: null,
    isSystem: true,
    action: "System completed sync with",
    target: "Contentful",
    time: "4h ago",
  },
  {
    user: "Sarah Jenkins",
    initials: "SJ",
    color: "blue",
    action: "joined the workspace",
    target: null,
    time: "Yesterday",
  },
];

const colorMap = {
  blue: { bg: "bg-blue-100", text: "text-blue-700" },
  purple: { bg: "bg-purple-100", text: "text-purple-700" },
} as const;

function Avatar({ item }: { item: ActivityItem }) {
  if (item.isSystem) {
    return (
      <div className="w-8 h-8 rounded-full bg-brand-50 flex items-center justify-center z-10 flex-shrink-0">
        <Link className="w-3.5 h-3.5 text-brand-500" />
      </div>
    );
  }

  if (item.user === "You") {
    return (
      <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center z-10 flex-shrink-0">
        <span className="text-xs font-medium text-brand-700">AL</span>
      </div>
    );
  }

  const colors = item.color ? colorMap[item.color] : { bg: "bg-stone-100", text: "text-stone-700" };

  return (
    <div
      className={`w-8 h-8 rounded-full ${colors.bg} flex items-center justify-center z-10 flex-shrink-0`}
    >
      <span className={`text-xs font-medium ${colors.text}`}>{item.initials}</span>
    </div>
  );
}

export function TeamActivity({ className }: { className?: string }) {
  return (
    <div className={`bg-surface-card rounded-xl p-6 shadow-soft ${className ?? ""}`}>
      {/* Header */}
      <h3 className="text-base font-semibold text-stone-900 mb-4">Team Activity</h3>

      {/* Timeline */}
      <div className="relative before:absolute before:inset-0 before:ml-4 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-stone-200 before:to-transparent">
        <div className="space-y-4">
          {activities.map((item, i) => (
            <div key={i} className="relative flex items-center gap-4">
              <Avatar item={item} />
              <div className="min-w-0">
                <p className="text-sm">
                  {item.isSystem ? (
                    <>
                      <span className="text-stone-600">{item.action}</span>{" "}
                      {item.target && (
                        <span className="font-medium text-brand-700">{item.target}</span>
                      )}
                    </>
                  ) : (
                    <>
                      <span className="font-medium text-stone-900">{item.user}</span>{" "}
                      <span className="text-stone-600">{item.action}</span>{" "}
                      {item.target && (
                        <span className="font-medium text-stone-800">{item.target}</span>
                      )}
                    </>
                  )}
                </p>
                <p className="text-xs text-stone-400 mt-0.5">{item.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
