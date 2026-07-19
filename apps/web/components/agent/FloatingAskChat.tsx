"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { MessageSquareText, Send, X } from "lucide-react";
import {
  sendAgentMessage,
  type AgentMessageResponse,
  type NlQueryResponse,
} from "@/lib/api/client";

const SUGGESTIONS = [
  "technical founder, AI infra, enterprise traction, no prior VC backing",
  "cold-start founder with strong execution signal",
  "compare Rivera Labs and Lee Analytics",
];

type ChatMessage =
  | { role: "user"; content: string }
  | {
      role: "assistant";
      content: string;
      mode?: AgentMessageResponse["mode"];
      skills_used?: string[];
      search?: NlQueryResponse | null;
    };

function SearchResults({ search }: { search: NlQueryResponse }) {
  return (
    <div className="mt-2 space-y-2 border-t border-line pt-2">
      {search.constraints.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {search.constraints.map((c) => (
            <span
              key={c}
              className="rounded-[2px] border border-line bg-background px-2 py-0.5 font-mono text-[10px] text-sub"
            >
              {c}
            </span>
          ))}
        </div>
      )}
      {search.results.length === 0 ? (
        <p className="text-[11px] text-sub">No opportunities matched these constraints.</p>
      ) : (
        search.results.slice(0, 5).map((r) => (
          <div key={r.opportunity_id} className="rounded-[2px] border border-line2 bg-background p-2 space-y-1">
            <div className="flex items-baseline justify-between gap-2">
              <Link
                href={`/opportunities/${r.opportunity_id}`}
                className="text-xs font-medium text-ink hover:underline"
              >
                {r.company_name}
                <span className="font-normal text-sub"> — {r.founder_name}</span>
              </Link>
              <span className="shrink-0 font-mono text-[10px] text-sub">
                {r.match_count}/{search.constraints.length}
              </span>
            </div>
            <ul className="space-y-0.5">
              {r.clause_matches.slice(0, 4).map((m, i) => (
                <li key={i} className="text-[10px] leading-snug text-sub">
                  <span className={m.matched ? "text-emerald-700" : "text-sub/70"}>
                    {m.matched ? "✓" : "✕"}
                  </span>{" "}
                  <span className="text-ink/80">{m.constraint}</span>
                  {m.explanation ? ` — ${m.explanation}` : ""}
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}

export function FloatingAskChat() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Ask the pipeline — filter deals in plain English, or ask a diligence question. Search returns per-clause matches; actions route to VC skills.",
      mode: "chat",
    },
  ]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  async function send(text?: string) {
    const content = (text ?? input).trim();
    if (!content || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content }]);
    setSending(true);
    try {
      const data = await sendAgentMessage(content);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: data.reply,
          mode: data.mode,
          skills_used: data.skills_used,
          search: data.search,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Agent API unreachable — is apps/api running?", mode: "chat" },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      {open && (
        <div
          className="flex w-[min(100vw-2.5rem,24rem)] flex-col overflow-hidden rounded-[2px] border border-line bg-surface shadow-[0_12px_40px_rgba(25,23,19,0.18)]"
          style={{ height: "min(70vh, 34rem)" }}
        >
          <header className="flex items-center justify-between border-b border-line px-4 py-3">
            <div>
              <p className="font-serif text-base font-semibold text-ink">Ask VC Brain</p>
              <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-sub">
                Search + agent
              </p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-[2px] p-1.5 text-sub hover:bg-muted hover:text-ink"
              aria-label="Close chat"
            >
              <X className="h-4 w-4" />
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <div
                  className={
                    m.role === "user"
                      ? "inline-block max-w-[92%] rounded-[2px] bg-ink px-3 py-2 text-left text-xs text-background"
                      : "inline-block max-w-[92%] rounded-[2px] border border-line2 bg-background px-3 py-2 text-left text-xs text-ink"
                  }
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                  {m.role === "assistant" && m.search && <SearchResults search={m.search} />}
                </div>
                {m.role === "assistant" && m.skills_used && m.skills_used.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {m.skills_used.map((s) => (
                      <span
                        key={s}
                        className="rounded-[2px] border border-line px-1.5 py-0.5 font-mono text-[9px] text-sub"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {messages.length <= 2 && (
            <div className="flex flex-wrap gap-1.5 border-t border-line2 px-3 py-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => send(s)}
                  disabled={sending}
                  className="max-w-full truncate rounded-[2px] border border-line px-2 py-1 text-left text-[10px] text-sub hover:border-ink hover:text-ink disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <form
            className="flex gap-2 border-t border-line px-3 py-3"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <input
              className="min-w-0 flex-1 rounded-[2px] border border-line bg-background px-3 py-2 text-xs text-ink placeholder:text-sub focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="Filter deals or ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="shrink-0 rounded-[2px] bg-ink px-3 py-2 text-background disabled:opacity-40"
              aria-label="Send"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex h-12 w-12 items-center justify-center rounded-full bg-ink text-background shadow-[0_8px_24px_rgba(25,23,19,0.25)] transition-transform hover:scale-105"
        aria-label={open ? "Close Ask VC Brain" : "Open Ask VC Brain"}
      >
        {open ? <X className="h-5 w-5" /> : <MessageSquareText className="h-5 w-5" />}
      </button>
    </div>
  );
}
