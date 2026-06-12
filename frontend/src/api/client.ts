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

export async function triggerRun(): Promise<{ status: string }> {
  const res = await fetch("/api/run", { method: "POST" });
  if (res.status === 409) throw new Error("A run is already in progress");
  if (!res.ok) throw new Error(`run ${res.status}`);
  return res.json();
}
