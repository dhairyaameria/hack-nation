import { getPipelineDashboard } from "@/lib/api/client";
import { OutboundSourcesView } from "@/components/dashboard/OutboundSourcesView";

export const dynamic = "force-dynamic";

export default async function OutboundSourcesPage() {
  const dashboard = await getPipelineDashboard();
  const open = dashboard.opportunities.filter(
    (o) => !["funded", "rejected"].includes(o.status)
  );

  return (
    <OutboundSourcesView
      thesisName={dashboard.active_thesis?.name ?? "No active thesis"}
      opportunities={open}
    />
  );
}
