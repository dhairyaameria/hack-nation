import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Truncate at a paragraph / sentence / word boundary — never mid-token. */
export function clipText(text: string, maxLen: number, ellipsis = true): string {
  const raw = text.trim()
  if (maxLen <= 0 || raw.length <= maxLen) return raw

  const budget = Math.max(1, maxLen - (ellipsis ? 1 : 0))
  let chunk = raw.slice(0, budget)
  const minKeep = Math.max(Math.floor(budget / 2), Math.min(40, Math.floor(budget / 3)))

  for (const sep of ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "] as const) {
    const idx = chunk.lastIndexOf(sep)
    if (idx >= minKeep) {
      chunk = sep.length === 2 && sep.endsWith(" ") ? chunk.slice(0, idx + 1) : chunk.slice(0, idx)
      break
    }
  }

  chunk = tidyIncompleteMarkdown(chunk)
  if (ellipsis && chunk && !/[…。.!?!:;]$/.test(chunk)) chunk += "…"
  return chunk
}

/** Scraped search hits → short prose for citation / web-research cards. */
export function plainSnippet(text: string, maxLen = 280): string {
  return clipText(stripMarkdownNoise(text), maxLen)
}

function stripMarkdownNoise(text: string): string {
  let s = text.replace(/\r\n?/g, "\n")
  s = s.replace(/!\[[^\]]*\]\([^)]+\)/g, "")
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
  s = s.replace(/^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$/gm, " ")
  s = s.replace(/^\s*\|.*\|\s*$/gm, (row) => ` ${row.replace(/\|/g, " ")} `)
  s = s.replace(/#{1,6}\s+/g, " ")
  s = s.replace(/^\s*([-*•]|\d+[.)])\s+/gm, "")
  s = s.replace(/(\*\*|__|\*|_|~~|`)/g, "")
  s = s.replace(/\|/g, " ")
  s = s.replace(/([.!?])([A-Z])/g, "$1 $2")
  return s.replace(/\s+/g, " ").trim()
}

/** Drop dangling bullets / open ** / partial [N] left by a hard cut or max_tokens stop. */
export function tidyIncompleteMarkdown(text: string): string {
  const emptyBullet = /^\s*([-*•]|\d+[.)])\s*$/
  let lines = text.split("\n")
  while (lines.length && emptyBullet.test(lines[lines.length - 1]!)) lines.pop()
  let chunk = lines.join("\n").trimEnd()

  if ((chunk.match(/\*\*/g) || []).length % 2 === 1) {
    const last = chunk.lastIndexOf("**")
    if (last !== -1) chunk = chunk.slice(0, last).trimEnd()
  }

  chunk = chunk.replace(/\[\d*$/, "").trimEnd()
  lines = chunk.split("\n")
  while (lines.length && emptyBullet.test(lines[lines.length - 1]!)) lines.pop()
  return lines.join("\n").trimEnd()
}

/** Confidential founder-pack sections — empty means withheld, not "analyst didn't write it". */
const FOUNDER_SENSITIVE_MEMO_SECTIONS = new Set([
  "Financials & round structure",
  "Cap table",
])

export type MemoGapKind = "withheld" | "insufficient_evidence"

/** Classify an empty memo section for badge + copy (works for old memos too). */
export function memoGapKind(title: string, _notDisclosed = false): MemoGapKind {
  // Title wins over legacy not_disclosed stamps on SWOT / exit / hypotheses.
  if (FOUNDER_SENSITIVE_MEMO_SECTIONS.has(title)) return "withheld"
  return "insufficient_evidence"
}

export function memoGapCopy(kind: MemoGapKind): string {
  if (kind === "withheld") {
    return "Not disclosed — the founder withheld this and no inference was made. This is a recorded fact about the memo, not a guess about the company."
  }
  return "Insufficient evidence in the source pack to write this section — no inference was fabricated."
}
