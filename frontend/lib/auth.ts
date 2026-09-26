import { jwtDecode } from "jwt-decode";

/**
 * Auth token utilities for Edubest frontend.
 *
 * Tokens are stored in:
 *  - localStorage: access + refresh tokens (persists across browser sessions)
 *  - cookie: access token only (read by middleware on the Edge runtime)
 *
 * Why both storages?
 *  localStorage → JavaScript-accessible for Axios interceptors
 *  Cookie       → HTTP-readable by Next.js middleware for server-side auth gating
 *
 * Security note: The cookie is set with SameSite=Lax and Secure (in production).
 * HttpOnly is intentionally NOT used for the access token because the JS
 * interceptor needs to read it.  The refresh token is kept only in localStorage
 * and is never sent as a cookie to reduce CSRF surface area.
 */

/* ── Storage keys ────────────────────────────────────────────────── */
const ACCESS_TOKEN_KEY = "edubest_access_token";
const REFRESH_TOKEN_KEY = "edubest_refresh_token";
const COOKIE_NAME = "edubest_access_token";

/* ── JWT payload shape ───────────────────────────────────────────── */
export interface DecodedToken {
  sub: string;           // user ID (UUID)
  email: string;
  role: string;
  tenant: string;        // tenant slug
  first_name: string;
  last_name: string;
  permissions: string[];
  exp: number;           // expiry (Unix seconds)
  iat: number;           // issued-at (Unix seconds)
}

/* ── Cookie helpers ──────────────────────────────────────────────── */

/** Sets `document.cookie` to store the access token for middleware */
function setCookie(value: string, expiresInSeconds: number): void {
  if (typeof document === "undefined") return;

  const expires = new Date(Date.now() + expiresInSeconds * 1000).toUTCString();
  const secure = window.location.protocol === "https:" ? "; Secure" : "";

  document.cookie = [
    `${COOKIE_NAME}=${encodeURIComponent(value)}`,
    `expires=${expires}`,
    "path=/",
    "SameSite=Lax",
    secure,
  ].join("; ");
}

/** Removes the access-token cookie by setting a past expiry date */
function removeCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax`;
}

/* ── Public API ──────────────────────────────────────────────────── */

/**
 * Retrieves the access token from localStorage.
 * Returns null if running on the server or if no token exists.
 */
export function getToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Retrieves the refresh token from localStorage.
 */
export function getRefreshToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Persists the access token to both localStorage and a cookie
 * (so middleware can read it without JS).
 *
 * @param token - raw JWT access token string
 */
export function setToken(token: string): void {
  if (typeof localStorage === "undefined") return;

  localStorage.setItem(ACCESS_TOKEN_KEY, token);

  // Mirror to cookie so the middleware Edge runtime can read it
  // Default to 15 minutes if we can't decode the expiry
  let ttlSeconds = 900;
  try {
    const payload = decodeToken(token);
    if (payload) {
      ttlSeconds = payload.exp - Math.floor(Date.now() / 1000);
    }
  } catch {
    // ignore decode errors; cookie will just expire sooner
  }

  setCookie(token, Math.max(ttlSeconds, 0));
}

/**
 * Persists the refresh token to localStorage only
 * (never stored in a cookie — reduces CSRF attack surface).
 *
 * @param token - raw JWT refresh token string
 */
export function setRefreshToken(token: string): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

/**
 * Removes both tokens from localStorage and clears the cookie.
 * Call this on logout or when a refresh fails.
 */
export function clearToken(): void {
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  removeCookie();
}

/**
 * Decodes (but does NOT verify) a JWT to extract the payload.
 * Verification happens on the backend; we just need the claims for UI logic.
 *
 * @param token - raw JWT string (defaults to stored access token)
 * @returns decoded payload or null on failure
 */
export function decodeToken(token?: string): DecodedToken | null {
  const raw = token ?? getToken();
  if (!raw) return null;

  try {
    return jwtDecode<DecodedToken>(raw);
  } catch {
    return null;
  }
}

/**
 * Returns true if the given token (or the stored token if none provided)
 * is expired or will expire within the next `bufferSeconds` seconds.
 *
 * @param token         - optional raw JWT string
 * @param bufferSeconds - early-expiry buffer (default: 60 s)
 */
export function isTokenExpired(
  token?: string,
  bufferSeconds: number = 60,
): boolean {
  const payload = decodeToken(token);
  if (!payload) return true; // no token → treat as expired

  const expiryMs = payload.exp * 1000;
  const bufferMs = bufferSeconds * 1000;

  return Date.now() + bufferMs >= expiryMs;
}

/**
 * Convenience: checks if a valid, non-expired token exists in storage.
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  return !!token && !isTokenExpired(token);
}
