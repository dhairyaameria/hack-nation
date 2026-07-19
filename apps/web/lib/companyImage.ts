/** Best-effort company logo URLs. Prefer real domains only — guessed hosts
 *  produce junk favicons that look pixelated when upscaled on cards. */

export function guessCompanyDomain(companyName: string, domain?: string | null): string | null {
  if (domain) {
    return domain
      .replace(/^https?:\/\//, "")
      .replace(/^www\./, "")
      .split("/")[0]
      .toLowerCase();
  }
  return null;
}

/** High-res logo candidates only. Empty → UI should show CompanyMark. */
export function companyImageCandidates(companyName: string, domain?: string | null): string[] {
  const host = guessCompanyDomain(companyName, domain);
  if (!host) return [];
  return [`https://logo.clearbit.com/${host}`];
}
