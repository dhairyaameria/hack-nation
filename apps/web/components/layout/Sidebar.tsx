"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Users, MessageSquareText, Settings } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Pipeline", icon: LayoutDashboard },
  { href: "/founders", label: "Founders", icon: Users },
  { href: "/agent", label: "Agent", icon: MessageSquareText },
  { href: "/settings/thesis", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r bg-muted/30 flex flex-col h-screen sticky top-0">
      <div className="px-5 py-5 border-b">
        <div className="font-semibold text-lg tracking-tight">VC Brain</div>
        <div className="text-xs text-muted-foreground">Maschmeyer Group</div>
      </div>
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-4 border-t text-xs text-muted-foreground">
        Deploying $100K checks in 24 hours.
      </div>
    </aside>
  );
}
