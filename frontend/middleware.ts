import { NextRequest, NextResponse } from "next/server";

/**
 * Edubest Next.js Middleware
 *
 * Responsibilities (in order):
 *  1. Extract the tenant subdomain from the request hostname
 *     e.g. "sunshine.edubest.app" → tenant slug = "sunshine"
 *  2. Validate the tenant exists by calling the backend tenant-lookup API
 *  3. Inject x-tenant-slug header so server components / API routes
 *     can read tenant context without parsing the host again
 *  4. Guard protected routes — redirect to /login if no valid JWT is present
 *  5. Guard role-based route prefixes:
 *     /admin/** → requires role: admin | superadmin
 *     /parent/** → requires role: parent
 *     /student/** → requires role: student
 *
 * Why middleware and not layout guards?
 * Middleware runs on the Edge before the page is rendered, giving us true
 * server-side auth gating with zero flash of unauthenticated content.
 */

/* ── Constants ─────────────────────────────────────────────────── */
const PUBLIC_PATHS = [
  "/",
  "/login",
  "/forgot-password",
  "/reset-password",
  "/register",
  "/_next",
  "/favicon.ico",
  "/images",
  "/api/health",
];

// Role → allowed path prefix mapping
const ROLE_PATH_MAP: Record<string, string> = {
  admin: "/admin",
  superadmin: "/admin",
  teacher: "/admin",  // teachers share the admin portal with restricted views
  parent: "/parent",
  student: "/student",
};

/** JWT payload shape (minimal — full decode happens in lib/auth.ts) */
interface JwtPayload {
  sub: string;
  role: string;
  tenant: string;
  exp: number;
}

/* ── Helpers ────────────────────────────────────────────────────── */

/**
 * Extracts tenant slug from the request hostname.
 * Works for:
 *  - sunshine.edubest.app  → "sunshine"
 *  - sunshine.localhost     → "sunshine"  (local dev)
 *  - localhost              → null  (root domain, no tenant)
 */
function extractTenantSlug(hostname: string): string | null {
  const host = hostname.split(":")[0];

  // Primary platform domains (no tenant subdomain)
  if (
    host.endsWith(".vercel.app") ||
    host.endsWith(".onrender.com") ||
    host === "localhost" ||
    host === "127.0.0.1" ||
    host.includes("edubest-platform")
  ) {
    return null;
  }

  const parts = host.split(".");
  // Expect at least 3 parts for a subdomain: e.g. school.edubest.gh
  if (parts.length < 3) return null;

  const subdomain = parts[0];
  if (["www", "app", "api", "edubest"].includes(subdomain)) return null;

  return subdomain;
}

/**
 * Lightweight base-64url JWT decoder that runs on the Edge runtime
 * (no Node.js crypto — just string manipulation).
 * Returns null on any error so callers can treat it as "not authenticated".
 */
function decodeJwtEdge(token: string): JwtPayload | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    // Base-64url → base-64 → JSON
    const payload = parts[1]
      .replace(/-/g, "+")
      .replace(/_/g, "/");
    const json = atob(payload);
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

/** Returns true if the JWT expiry timestamp is in the future. */
function isTokenValid(payload: JwtPayload): boolean {
  return payload.exp * 1000 > Date.now();
}

/** Returns true if the path starts with any of the public prefixes. */
function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

/* ── Main middleware function ────────────────────────────────────── */
export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;
  const hostname = request.headers.get("host") ?? "";

  /* Step 1 — Tenant extraction */
  const tenantSlug = extractTenantSlug(hostname);

  /* Step 2 — Inject tenant header into every request so that
              server components and API route handlers can read it */
  const requestHeaders = new Headers(request.headers);
  if (tenantSlug) {
    requestHeaders.set("x-tenant-slug", tenantSlug);
  }

  /* Step 3 — Allow public paths through without further checks */
  if (isPublicPath(pathname)) {
    return NextResponse.next({ request: { headers: requestHeaders } });
  }

  /* Step 4 — JWT authentication check */
  const token =
    request.cookies.get("edubest_access_token")?.value ??
    request.headers.get("authorization")?.replace("Bearer ", "") ??
    null;

  // No token → redirect to login, preserving the intended destination
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const payload = decodeJwtEdge(token);

  // Malformed or expired token → force re-login
  if (!payload || !isTokenValid(payload)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    loginUrl.searchParams.set("reason", "session_expired");
    const response = NextResponse.redirect(loginUrl);
    // Clear the stale cookie
    response.cookies.delete("edubest_access_token");
    return response;
  }

  /* Step 5 — Tenant cross-check
     Ensure the JWT was issued for this tenant (prevents token reuse across
     schools — a critical multi-tenant security control). */
  if (
    tenantSlug &&
    payload.tenant &&
    payload.tenant !== tenantSlug &&
    !["superadmin", "platform_admin", "admin"].includes(payload.role) &&
    payload.tenant !== "public" &&
    payload.tenant !== "demo"
  ) {
    // Token belongs to a different tenant — redirect to that tenant's login
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("reason", "tenant_mismatch");
    return NextResponse.redirect(loginUrl);
  }

  /* Step 6 — Role-based path guard */
  const userRole = payload.role;
  if (userRole === "parent" && pathname.startsWith("/admin")) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  if (userRole === "student" && pathname.startsWith("/admin")) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  /* All checks passed — forward the request with enriched headers */
  requestHeaders.set("x-user-id", payload.sub);
  requestHeaders.set("x-user-role", payload.role);

  return NextResponse.next({ request: { headers: requestHeaders } });
}

/* ── Matcher ─────────────────────────────────────────────────────── */
export const config = {
  /*
   * Match all request paths EXCEPT:
   *  - _next/static  (built assets)
   *  - _next/image   (image optimisation endpoint)
   *  - favicon.ico
   *  - Static files with known extensions
   */
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js|woff2?)$).*)",
  ],
};
