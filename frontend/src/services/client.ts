export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  // Some endpoints may return 204 or no body
  const ct = res.headers.get("content-type");
  if (ct && ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return undefined as unknown as T;
}

