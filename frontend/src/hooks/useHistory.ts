import { useCallback, useEffect, useState } from "react";
import { fetchHistory } from "../api/client";
import type { RunHistoryItem } from "../state/types";

/** Past runs list; refetches whenever runStatus flips to completed/failed. */
export function useHistory(runStatus: string) {
  const [items, setItems] = useState<RunHistoryItem[]>([]);

  const refresh = useCallback(() => {
    fetchHistory().then(setItems).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, runStatus === "completed", runStatus === "failed"]);

  return items;
}
