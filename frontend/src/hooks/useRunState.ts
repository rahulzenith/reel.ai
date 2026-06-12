import { useReducer } from "react";
import { initialState, reducer } from "../state/reducer";
import { useWebSocket } from "./useWebSocket";

export function useRunState() {
  const [state, dispatch] = useReducer(reducer, initialState);
  useWebSocket(dispatch);
  return state;
}
