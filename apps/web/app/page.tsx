import { getPipelineDashboard } from "@/lib/api/client";
import { OutboundSourcesView } from "@/components/dashboard/OutboundSourcesView";

export const dynamic = "force-dynamic";

export default async function OutboundSourcesPage() {
  const dashboard = await getPipelineDashboard();

  return (
    <OutboundSourcesView
      thesisName={dashboard.active_thesis.name}
      opportunities={dashboard.opportunities}
    />
  );
}
