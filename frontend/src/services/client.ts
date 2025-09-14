export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('uf_token') : null;
  
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token && { "Authorization": `Bearer ${token}` }),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    // Try to surface structured error details when available
    try {
      const data = await res.clone().json();
      const err: any = new Error(
        `API ${res.status}: ${typeof data?.detail === 'string' ? data.detail : res.statusText}`
      );
      err.status = res.status;
      err.data = data;
      throw err;
    } catch {
      const text = await res.text().catch(() => "");
      const err: any = new Error(`API ${res.status}: ${text || res.statusText}`);
      err.status = res.status;
      throw err;
    }
  }
  // Some endpoints may return 204 or no body
  const ct = res.headers.get("content-type");
  if (ct && ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return undefined as unknown as T;
}
