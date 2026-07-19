import { redirect } from "next/navigation";

/** Merged into the floating Ask chat (bottom-right). */
export default function AgentChatPage() {
  redirect("/outbound");
}
