"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

/**
 * Toggles the `dark` class on <html>, which is what the `dark:` variant and
 * the .dark token block in globals.css key off. The initial class is set by
 * the inline script in layout.tsx before paint, so this only has to read it.
 */
export function ThemeToggle() {
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
      // private mode / storage disabled — theme just won't persist
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={dark}
      className="flex w-full items-center gap-2 rounded-[2px] border border-line px-3 py-2 font-mono text-[11px] uppercase tracking-[0.08em] text-sub transition-colors hover:border-ink hover:text-ink"
    >
      {dark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
      {dark ? "Light" : "Dark"}
    </button>
  );
}
