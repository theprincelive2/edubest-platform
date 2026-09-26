import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from "axios";
import { getToken, setToken, clearToken } from "@/lib/auth";

/**
 * Edubest API Axios Instance
 *
 * Single source-of-truth for all HTTP calls to the Django backend.
 *
 * Features:
 *  - Base URL pulled from NEXT_PUBLIC_API_URL environment variable
 *  - Request interceptor: auto-attach Bearer token + x-tenant-slug header
 *  - Response interceptor: silent token refresh on 401, then retry original request
 *  - Structured error normalisation so every caller gets a consistent ApiError shape
 *
 * Token refresh strategy:
 *  We keep a single in-flight refresh promise so that if multiple requests
 *  fail simultaneously with 401, we only call /auth/token/refresh/ once
 *  and queue the retries behind it.
 */

/* ── Environment ─────────────────────────────────────────────────── */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/* ── Custom error type ───────────────────────────────────────────── */
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  detail?: unknown;
}

/** Wraps any Axios error into our normalised ApiError shape */
function normaliseError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as Record<string, unknown> | undefined;
    return {
      message:
        (data?.detail as string) ??
        (data?.message as string) ??
        error.message ??
        "An unexpected error occurred.",
      code: (data?.code as string) ?? undefined,
      status: error.response?.status,
      detail: data,
    };
  }
  if (error instanceof Error) {
    return { message: error.message };
  }
  return { message: "An unexpected error occurred." };
}

/* ── Refresh token singleton ─────────────────────────────────────── */
let refreshPromise: Promise<string> | null = null;

/**
 * Calls /auth/token/refresh/ with the stored refresh token.
 * Returns the new access token string.
 * Throws if refresh fails (user will be logged out by the interceptor).
 */
async function refreshAccessToken(): Promise<string> {
  // Deduplicate concurrent refresh attempts
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const refreshToken =
        typeof window !== "undefined"
          ? localStorage.getItem("edubest_refresh_token")
          : null;

      if (!refreshToken) throw new Error("No refresh token available.");

      const response = await axios.post<{ access: string }>(
        `${API_BASE_URL}/auth/token/refresh/`,
        { refresh: refreshToken },
      );

      const newAccessToken = response.data.access;
      setToken(newAccessToken);
      return newAccessToken;
    } finally {
      // Always clear the singleton regardless of success/failure
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/* ── Axios instance factory ──────────────────────────────────────── */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000, // 30 s — generous for slow school networks
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

/* ── Request interceptor ─────────────────────────────────────────── */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    // Attach JWT access token if present
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Inject tenant slug from localStorage (set during login / tenant resolution)
    if (typeof window !== "undefined") {
      const tenantSlug = localStorage.getItem("edubest_tenant_slug");
      if (tenantSlug) {
        config.headers["X-Tenant-Slug"] = tenantSlug;
      }
    }

    return config;
  },
  (error) => Promise.reject(normaliseError(error)),
);

/* ── Response interceptor ────────────────────────────────────────── */
api.interceptors.response.use(
  // Success — pass through unchanged
  (response: AxiosResponse) => response,

  // Error — attempt silent refresh on 401, propagate everything else
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & {
      _retried?: boolean;
    };

    // Only attempt one refresh per request to avoid infinite loops
    if (error.response?.status === 401 && !originalRequest._retried) {
      originalRequest._retried = true;

      try {
        const newToken = await refreshAccessToken();
        // Patch the Authorization header and retry
        if (originalRequest.headers) {
          (originalRequest.headers as Record<string, string>)[
            "Authorization"
          ] = `Bearer ${newToken}`;
        }
        return api(originalRequest);
      } catch {
        // Refresh failed → clear local auth state and send user to login
        clearToken();
        if (typeof window !== "undefined") {
          window.location.href = "/login?reason=session_expired";
        }
        return Promise.reject(normaliseError(error));
      }
    }

    return Promise.reject(normaliseError(error));
  },
);

/* ── Typed convenience wrappers ─────────────────────────────────── */

/**
 * Generic GET helper.
 * Usage: const data = await apiGet<Student[]>("/students/");
 */
export async function apiGet<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.get<T>(url, config);
  return response.data;
}

/**
 * Generic POST helper.
 * Usage: const student = await apiPost<Student>("/students/", payload);
 */
export async function apiPost<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.post<T>(url, data, config);
  return response.data;
}

/**
 * Generic PATCH helper (partial update — preferred over PUT in REST APIs).
 */
export async function apiPatch<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.patch<T>(url, data, config);
  return response.data;
}

/**
 * Generic PUT helper (full replacement).
 */
export async function apiPut<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.put<T>(url, data, config);
  return response.data;
}

/**
 * Generic DELETE helper.
 */
export async function apiDelete<T = void>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.delete<T>(url, config);
  return response.data;
}

export { api as default, normaliseError };
