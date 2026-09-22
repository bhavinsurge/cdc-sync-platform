const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8007";

export type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: { code: string; message: string; details?: unknown } };

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("river_access");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("river_access", token);
  else localStorage.removeItem("river_access");
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResult<T>> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  const json = (await res.json()) as ApiResult<T>;
  return json;
}

export { API_BASE };
