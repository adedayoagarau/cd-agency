"use client";

export function Greeting({ name }: { name: string }) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="mb-8">
      <h1 className="font-serif text-2xl md:text-3xl font-semibold text-stone-900 tracking-tight mb-2">
        {greeting}, {name}
      </h1>
      <p className="text-stone-500">Here&apos;s what&apos;s happening in your content workspace today.</p>
    </div>
  );
}
