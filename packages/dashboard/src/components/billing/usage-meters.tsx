export function UsageMeters({
  meters,
}: {
  meters: { label: string; current: number; max: number; unit: string }[];
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {meters.map((meter) => {
        const pct = Math.round((meter.current / meter.max) * 100);
        let barColor = "bg-brand-500";
        if (pct > 95) barColor = "bg-rose-500";
        else if (pct > 80) barColor = "bg-amber-500";

        return (
          <div key={meter.label}>
            <p className="text-sm font-medium text-stone-600 mb-1">
              {meter.label}
            </p>
            <p className="text-lg font-semibold text-stone-900 mb-2">
              {meter.current} / {meter.max} {meter.unit}
            </p>
            <div className="h-2 rounded-full bg-stone-100 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${barColor}`}
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
            <p className="text-xs text-stone-400 text-right mt-1">{pct}%</p>
          </div>
        );
      })}
    </div>
  );
}
