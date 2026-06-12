// WS URL derives from the page host so the Vite proxy (dev) or same-origin
// deployment (prod) both work without hardcoding the backend port.
export function wsUrl(): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/ws`;
}
