/**
 * Typed fetch wrapper for the FastAPI backend.
 *
 * - In the browser, calls go through Next.js rewrites at ``/api/v1/*``.
 * - On the server, calls go direct to the API host (``API_BASE``).
 * - Credentials are sent so JWT cookies (W1-002) reach the backend.
 */

const BROWSER_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api/v1";
const SERVER_BASE = (process.env.API_BASE ?? "http://localhost:8000") + "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | Record<string, unknown> | null;
  query?: Record<string, string | number | boolean | undefined>;
}

function buildUrl(path: string, query?: ApiFetchOptions["query"]): string {
  const base = typeof window === "undefined" ? SERVER_BASE : BROWSER_BASE;
  const url = path.startsWith("http") ? path : `${base}${path}`;
  if (!query) return url;
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) {
    if (v === undefined) continue;
    search.append(k, String(v));
  }
  const qs = search.toString();
  return qs ? `${url}?${qs}` : url;
}

export async function apiFetch<T>(
  path: string,
  { body, query, headers, ...init }: ApiFetchOptions = {},
): Promise<T> {
  const url = buildUrl(path, query);
  const isJsonBody =
    body !== null &&
    body !== undefined &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer);

  const res = await fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      ...(isJsonBody ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: isJsonBody ? JSON.stringify(body) : (body as BodyInit | null | undefined),
  });

  if (!res.ok) {
    const errBody = await res.json().catch((err) => { console.error('API error parsing response body:', err); return undefined; });
    const message =
      (errBody as { error?: { message?: string } } | undefined)?.error?.message ??
      res.statusText ??
      `HTTP ${res.status}`;
    throw new ApiError(res.status, message, errBody);
  }

  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return (await res.text()) as unknown as T;
  }
  return (await res.json()) as T;
}
