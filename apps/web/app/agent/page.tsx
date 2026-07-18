"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  skills_used?: string[];
}

export default function AgentChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Ask me anything about the pipeline — e.g. \"compare Rivera Labs and Lee Analytics\" or \"what's NovaMetrics' trust score?\" I route to Cursor skills and cite evidence.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/agent/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.content }),
      });
      const data = await res.json();
      setMessages((m) => [
        ...m,
        { role: "assistant", content: data.reply, skills_used: data.skills_used },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Agent API unreachable — is apps/api running?" },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto flex flex-col h-[calc(100vh-4rem)]">
      <h1 className="text-2xl font-semibold tracking-tight mb-4">VC Agent Chat</h1>
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={
                m.role === "user"
                  ? "inline-block bg-primary text-primary-foreground rounded-lg px-3 py-2 text-sm max-w-md"
                  : "inline-block bg-muted rounded-lg px-3 py-2 text-sm max-w-md"
              }
            >
              {m.content}
            </div>
            {m.skills_used && m.skills_used.length > 0 && (
              <div className="mt-1 flex gap-1 flex-wrap">
                {m.skills_used.map((s) => (
                  <Badge key={s} variant="outline" className="text-[10px]">
                    {s}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2 pt-4 border-t mt-4">
        <input
          className="flex-1 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
          placeholder="Ask the VC Agent…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={sending}
        />
        <Button onClick={send} disabled={sending} size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
