import type { RunHistoryItem, RunSnapshot } from "../state/types";

export async function fetchStatus(): Promise<RunSnapshot> {
  const res = await fetch("/api/status");
  if (!res.ok) throw new Error(`status ${res.status}`);
  return res.json();
}

export async function fetchHistory(limit = 20): Promise<RunHistoryItem[]> {
  const res = await fetch(`/api/history?limit=${limit}`);
  if (!res.ok) throw new Error(`history ${res.status}`);
  return res.json();
}

export async function triggerRun(topic?: string, content?: string): Promise<{ status: string }> {
  const hasBrief = Boolean(topic?.trim() || content?.trim());
  const res = await fetch("/api/run", {
    method: "POST",
    ...(hasBrief && {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: topic?.trim() || null, content: content?.trim() || null }),
    }),
  });
  if (res.status === 409) throw new Error("A run is already in progress");
  if (!res.ok) throw new Error(`run ${res.status}`);
  return res.json();
}
