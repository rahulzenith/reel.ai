export type AgentStatus = "waiting" | "running" | "done" | "error";

export interface Scores {
  hook_score: number;
  retention_score: number;
  clarity_score: number;
}

// Discriminated union of everything the backend broadcasts
export type WsEvent =
  | { type: "run_started"; run_id: string; trigger: string; log?: string }
  | { type: "node_status"; node: string; status: AgentStatus; log?: string }
  | { type: "topic_selected"; topic: string; source: string; log?: string }
  | { type: "script_preview"; script: Record<string, unknown>; log?: string }
  | { type: "eval_scores"; scores: Scores; passed: boolean; retry_count: number; feedback: string; log?: string }
  | { type: "run_complete"; run_id: string; video_path: string | null; youtube_url: string | null; dry_run: boolean; log?: string }
  | { type: "run_error"; run_id: string; error: string; log?: string };

// Shape returned by GET /api/status (used to rehydrate on reload/reconnect)
export interface RunSnapshot {
  run_id: string | null;
  run_status: "idle" | "running" | "completed" | "failed";
  topic: string | null;
  topic_source: string | null;
  nodes: Record<string, AgentStatus>;
  scores: Scores | null;
  retry_count: number;
  video_path: string | null;
  youtube_url: string | null;
  logs: string[];
  publish_mode: string;
  next_scheduled_run: string | null;
}

export interface RunHistoryItem {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: string;
  trigger: string | null;
  topic: string | null;
  topic_source: string | null;
  hook_score: number | null;
  retention_score: number | null;
  clarity_score: number | null;
  retry_count: number | null;
  video_path: string | null;
  youtube_url: string | null;
  publish_mode: string | null;
  error: string | null;
}

export const AGENTS = [
  { id: "trend_scout", label: "Trend scout", sub: "Tavily / Google Trends / curated" },
  { id: "script_writer", label: "Script writer", sub: "RAG patterns + learnings + style" },
  { id: "evaluator", label: "Evaluator", sub: "LLM judge — hook gate at 0.7" },
  { id: "voice_generator", label: "Voice generator", sub: "ElevenLabs TTS" },
  { id: "broll_selector", label: "B-roll selector", sub: "Pexels / generated clips" },
  { id: "assembler", label: "Video assembler", sub: "MoviePy 9:16 + captions" },
  { id: "publisher", label: "Publisher", sub: "YouTube Shorts / dry run" },
] as const;
