"use client";

import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import type { FounderScorePoint } from "@/lib/types";

export function ScoreTrendChart({ history }: { history: FounderScorePoint[] }) {
  const data = history.map((p) => ({
    date: new Date(p.recorded_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    score: Math.round(p.score * 100),
  }));

  return (
    <div className="h-32 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Tooltip />
          <Line type="monotone" dataKey="score" stroke="#2f9e6e" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
