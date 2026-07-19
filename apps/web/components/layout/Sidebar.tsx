"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "./ThemeToggle";
import { Briefcase, LayoutDashboard, Users, CircleUser, UploadCloud, FileText, Home } from "lucide-react";

const NAV_ITEMS = [
  { href: "/home", label: "Home", icon: Home },
  { href: "/apply", label: "Inbound Sources", icon: UploadCloud },
  { href: "/outbound", label: "Outbound Sources", icon: LayoutDashboard },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/memos", label: "Investment Memos", icon: FileText },
  { href: "/founders", label: "Founder Book", icon: Users },
  { href: "/profile", label: "Profile", icon: CircleUser },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r border-line bg-sidebar text-sidebar-foreground flex flex-col h-screen sticky top-0">
      <Link href="/" className="px-5 py-5 border-b border-sidebar-border block hover:opacity-90 transition-opacity">
        <div className="font-semibold text-lg tracking-tight text-foreground">
          Brain <span className="text-brand">Venture</span>
        </div>
      </Link>
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground shadow-[0_0_0_1px_var(--brand)]"
                  : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-4 border-t space-y-3">
        <ThemeToggle />
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-semibold"
            aria-hidden
          >
            DA
          </div>
          <div className="min-w-0">
            <div className="text-sm font-medium truncate">Marc Andreessen</div>
            <div className="text-xs text-muted-foreground truncate">Investor · Brain Venture</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
