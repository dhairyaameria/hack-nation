"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

/** Compact theme control for the public landing header. */
export function LandingThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {
      // ignore
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={dark}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      className="inline-flex items-center gap-2 rounded-[2px] border border-[var(--landing-line)] px-3 py-2 font-mono text-[11px] uppercase tracking-[0.08em] text-[var(--landing-muted)] transition-colors hover:border-[var(--landing-green)] hover:text-[var(--landing-fg)]"
    >
      {dark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
      {dark ? "Light" : "Dark"}
    </button>
  );
}
