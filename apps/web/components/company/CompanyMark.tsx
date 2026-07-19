"use client";

/** Soft letter-mark when no real company logo is available. */
export function CompanyMark({
  name,
  className = "",
}: {
  name: string;
  className?: string;
}) {
  const initial = (name || "?").trim().charAt(0).toUpperCase() || "?";
  // Stable pastel from name — keeps cards varied without looking random each render
  const hue = Array.from(name || "A").reduce((a, c) => a + c.charCodeAt(0), 0) % 360;

  return (
    <div
      className={`relative flex h-full w-full items-center justify-center overflow-hidden ${className}`}
      style={{
        background: `linear-gradient(145deg, hsl(${hue} 18% 92%) 0%, hsl(${(hue + 40) % 360} 14% 86%) 100%)`,
      }}
      aria-hidden
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(circle at 30% 20%, rgba(255,255,255,0.7), transparent 55%), radial-gradient(circle at 80% 90%, rgba(0,0,0,0.04), transparent 45%)",
        }}
      />
      <span
        className="relative font-serif text-5xl font-semibold tracking-tight"
        style={{ color: `hsl(${hue} 22% 32%)` }}
      >
        {initial}
      </span>
    </div>
  );
}
