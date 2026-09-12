export function cadacCallbackUrl(): string | null {
  const search =
    (globalThis as { location?: { search?: string } }).location?.search ?? "";
  const id = new URLSearchParams(search).get("cadacSession");
  if (!id) return null;
  return `http://127.0.0.1:8001/handshake/sessions/${id}/complete`;
}

export function openNewIfCadacSession(openNew: () => void): void {
  if (cadacCallbackUrl()) openNew();
}
