import type { AgentStatus, RunSnapshot, Scores, ScriptData, WsEvent } from "./types";

export interface RunState {
  connected: boolean;
  runStatus: "idle" | "running" | "completed" | "failed";
  runId: string | null;
  topic: string | null;
  topicSource: string | null;
  nodes: Record<string, AgentStatus>;
  script: ScriptData | null;
  scores: Scores | null;
  retryCount: number;
  evalFeedback: string | null;
  videoPath: string | null;
  youtubeUrl: string | null;
  dryRun: boolean;
  logs: string[];
  publishMode: string;
  nextScheduledRun: string | null;
}

export const initialState: RunState = {
  connected: false,
  runStatus: "idle",
  runId: null,
  topic: null,
  topicSource: null,
  nodes: {},
  script: null,
  scores: null,
  retryCount: 0,
  evalFeedback: null,
  videoPath: null,
  youtubeUrl: null,
  dryRun: true,
  logs: [],
  publishMode: "dry_run",
  nextScheduledRun: null,
};

export type Action =
  | { kind: "ws_event"; event: WsEvent }
  | { kind: "connection"; connected: boolean }
  | { kind: "snapshot"; snapshot: RunSnapshot };

const MAX_LOGS = 200;

function appendLog(logs: string[], line?: string): string[] {
  if (!line) return logs;
  return [...logs.slice(-(MAX_LOGS - 1)), line];
}

export function reducer(state: RunState, action: Action): RunState {
  switch (action.kind) {
    case "connection":
      return { ...state, connected: action.connected };

    case "snapshot": {
      const s = action.snapshot;
      return {
        ...state,
        runStatus: s.run_status,
        runId: s.run_id,
        topic: s.topic,
        topicSource: s.topic_source,
        nodes: s.nodes ?? {},
        script: s.script,
        scores: s.scores,
        evalFeedback: s.eval_feedback,
        retryCount: s.retry_count,
        videoPath: s.video_path,
        youtubeUrl: s.youtube_url,
        logs: s.logs ?? [],
        publishMode: s.publish_mode,
        nextScheduledRun: s.next_scheduled_run,
      };
    }

    case "ws_event": {
      const e = action.event;
      const logs = appendLog(state.logs, e.log);
      switch (e.type) {
        case "run_started":
          return {
            ...initialState,
            connected: state.connected,
            publishMode: state.publishMode,
            nextScheduledRun: state.nextScheduledRun,
            runStatus: "running",
            runId: e.run_id,
            logs: [e.log ?? "Run started"],
          };
        case "node_status":
          return { ...state, nodes: { ...state.nodes, [e.node]: e.status }, logs };
        case "topic_selected":
          return { ...state, topic: e.topic, topicSource: e.source, logs };
        case "script_preview":
          return { ...state, script: e.script, logs };
        case "eval_scores":
          return { ...state, scores: e.scores, retryCount: e.retry_count, evalFeedback: e.feedback, logs };
        case "run_complete":
          return { ...state, runStatus: "completed", videoPath: e.video_path, youtubeUrl: e.youtube_url, dryRun: e.dry_run, logs };
        case "run_error":
          return { ...state, runStatus: "failed", logs };
        default:
          return { ...state, logs };
      }
    }
  }
}
