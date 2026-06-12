import { useEffect, useRef } from "react";
import { wsUrl } from "../api/ws";
import { fetchStatus } from "../api/client";
import type { Action } from "../state/reducer";
import type { WsEvent } from "../state/types";

const BACKOFF_START_MS = 1000;
const BACKOFF_MAX_MS = 10000;

/** Connects to /ws, dispatches parsed events, reconnects with backoff,
 * and rehydrates from GET /api/status on every (re)connect. */
export function useWebSocket(dispatch: (a: Action) => void) {
  const backoff = useRef(BACKOFF_START_MS);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: number | undefined;
    let closed = false;

    const connect = () => {
      ws = new WebSocket(wsUrl());

      ws.onopen = async () => {
        backoff.current = BACKOFF_START_MS;
        dispatch({ kind: "connection", connected: true });
        try {
          dispatch({ kind: "snapshot", snapshot: await fetchStatus() });
        } catch {
          /* backend briefly unavailable — events will still stream */
        }
      };

      ws.onmessage = (e) => {
        try {
          const event: WsEvent = JSON.parse(e.data);
          dispatch({ kind: "ws_event", event });
        } catch {
          /* ignore malformed frames */
        }
      };

      ws.onclose = () => {
        dispatch({ kind: "connection", connected: false });
        if (closed) return;
        timer = window.setTimeout(connect, backoff.current);
        backoff.current = Math.min(backoff.current * 2, BACKOFF_MAX_MS);
      };
    };

    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      ws?.close();
    };
  }, [dispatch]);
}
