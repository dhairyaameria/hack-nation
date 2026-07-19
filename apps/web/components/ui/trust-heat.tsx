"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { TRUST_COLOR, type TrustLevel } from "./ds";

export function TrustHeat({
  cells,
  size = 10,
  withTip = false,
  className,
}: {
  cells: { label: string; level: TrustLevel }[];
  size?: number;
  withTip?: boolean;
  className?: string;
}) {
  const [tip, setTip] = useState<string | null>(null);
  return (
    <div className={cn("flex items-center gap-4", className)}>
      <div className="flex gap-1" title={withTip ? undefined : "trust by claim category"}>
        {cells.map((c, i) => (
          <span
            key={i}
            className="inline-block cursor-pointer rounded-[2px] transition-transform hover:scale-[1.18] hover:outline hover:outline-1 hover:outline-ink"
            style={{ width: size, height: size, background: TRUST_COLOR[c.level] }}
            title={withTip ? undefined : c.label}
            onMouseEnter={() => setTip(c.label)}
            onMouseLeave={() => setTip(null)}
          />
        ))}
      </div>
      {withTip && (
        <div className="min-w-[180px] rounded-[2px] border border-line bg-background px-2.5 py-1 font-mono text-[11px] text-ink">
          {tip ?? "← hover a cell"}
        </div>
      )}
    </div>
  );
}
