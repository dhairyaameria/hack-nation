"use client";

import { usePathname } from "next/navigation";
import { FloatingAskChat } from "@/components/agent/FloatingAskChat";
import { Sidebar } from "@/components/layout/Sidebar";

/** Landing (`/`) is full-bleed without the app chrome; everything else gets the sidebar. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  if (isLanding) {
    return <div className="min-h-full w-full">{children}</div>;
  }

  return (
    <>
      <Sidebar />
      <main className="flex-1 min-w-0">{children}</main>
      <FloatingAskChat />
    </>
  );
}
