export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-surface-bg min-h-screen flex items-center justify-center">
      <div className="max-w-xl w-full px-4">{children}</div>
    </div>
  );
}
