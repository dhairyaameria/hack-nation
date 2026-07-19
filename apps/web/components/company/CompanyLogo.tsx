"use client";

import { useState } from "react";
import { CompanyMark } from "@/components/company/CompanyMark";
import { companyImageCandidates } from "@/lib/companyImage";

export function CompanyLogo({
  name,
  domain,
  className = "h-14 w-14",
}: {
  name: string;
  domain?: string | null;
  className?: string;
}) {
  const candidates = companyImageCandidates(name, domain);
  const [failed, setFailed] = useState(false);
  const src = !failed && candidates[0] ? candidates[0] : null;

  return (
    <div
      className={`flex shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border ${className}`}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt=""
          className="h-full w-full object-contain bg-muted/30 p-2"
          onError={() => setFailed(true)}
        />
      ) : (
        <CompanyMark name={name} />
      )}
    </div>
  );
}
