import { redirect } from "next/navigation";

/** Sourcing UI lives under Outbound Sources → Find Lead. */
export default function SourcingRedirectPage() {
  redirect("/outbound");
}
