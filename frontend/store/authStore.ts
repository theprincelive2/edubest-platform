import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import {
  setToken,
  setRefreshToken,
  clearToken,
  decodeToken,
} from "@/lib/auth";
import type { User, LoginResponse, UserRole, Permission } from "@/types";

/**
 * Edubest Auth Zustand Store
 *
 * Manages all authentication state for the client.
 *
 * Persistence strategy:
 *  - The store is persisted to localStorage under the key "edubest-auth"
 *  - Sensitive data (the raw access/refresh token strings) are stored separately
 *    by lib/auth.ts — the store only holds the decoded user object and a flag.
 *  - On hydration, we re-validate the stored token before trusting the state.
 *
 * Why Zustand instead of context?
 *  Zustand avoids the context re-render cascade. Components subscribe to only
 *  the slices they need, so an unread-notification counter updating doesn't
 *  re-render the entire tree.
 */

interface AuthState {
  /** Decoded user object from the JWT — null when logged out */
  user: User | null;

  /** The raw access token string (kept for Axios interceptor convenience) */
  token: string | null;

  /** Tenant slug this session belongs to */
  tenant: string | null;

  /** Tracks whether we've completed the initial auth hydration check */
  isHydrated: boolean;

  /** True while a login/logout network request is in flight */
  isLoading: boolean;
}

interface AuthActions {
  /**
   * Called by the login page after a successful /auth/login/ response.
   * Stores tokens in localStorage/cookie (via lib/auth.ts) and updates state.
   */
  login: (response: LoginResponse) => void;

  /**
   * Clears all local auth state and tokens.
   * The calling component is responsible for redirecting to /login.
   */
  logout: () => void;

  /**
   * Partial update of the user object — used by the profile settings page
   * to reflect name/avatar changes without requiring a full re-login.
   */
  updateProfile: (updates: Partial<User>) => void;

  /**
   * Updates only the access token (used after a silent token refresh).
   */
  updateToken: (newToken: string) => void;

  /** Marks hydration as complete (called in root layout useEffect). */
  setHydrated: () => void;

  /** Sets loading state during async operations. */
  setLoading: (loading: boolean) => void;

  /* ── Permission helpers (avoids importing decodeToken everywhere) ── */

  /** Returns true if the current user has the given role. */
  hasRole: (role: UserRole | UserRole[]) => boolean;

  /** Returns true if the current user has the given permission string. */
  hasPermission: (permission: Permission) => boolean;

  /** Returns true if the current user is authenticated (non-null user). */
  isAuthenticated: () => boolean;
}

type AuthStore = AuthState & AuthActions;

/* ── Store ───────────────────────────────────────────────────────── */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      /* ── Initial state ─────────────────────────────────────────── */
      user: null,
      token: null,
      tenant: null,
      isHydrated: false,
      isLoading: false,

      /* ── Actions ───────────────────────────────────────────────── */
      login: (response: LoginResponse) => {
        const { tokens, user } = response;

        // Persist tokens to localStorage + cookie so middleware can read them
        setToken(tokens.access);
        setRefreshToken(tokens.refresh);

        // Also persist the tenant slug for Axios header injection
        if (typeof localStorage !== "undefined") {
          localStorage.setItem("edubest_tenant_slug", user.tenant);
        }

        set({
          user,
          token: tokens.access,
          tenant: user.tenant,
          isLoading: false,
        });
      },

      logout: () => {
        clearToken();
        if (typeof localStorage !== "undefined") {
          localStorage.removeItem("edubest_tenant_slug");
        }
        set({ user: null, token: null, tenant: null });
      },

      updateProfile: (updates: Partial<User>) => {
        const currentUser = get().user;
        if (!currentUser) return;
        set({ user: { ...currentUser, ...updates } });
      },

      updateToken: (newToken: string) => {
        setToken(newToken);
        // Re-decode to pick up any claim changes (rare but possible)
        const payload = decodeToken(newToken);
        set({ token: newToken });
        if (payload && get().user) {
          // Sync role/permissions in case the backend updated them
          set((state) => ({
            user: state.user
              ? {
                  ...state.user,
                  role: (payload.role as User["role"]) ?? state.user.role,
                  permissions: payload.permissions ?? state.user.permissions,
                }
              : null,
          }));
        }
      },

      setHydrated: () => set({ isHydrated: true }),

      setLoading: (loading: boolean) => set({ isLoading: loading }),

      /* ── Permission helpers ─────────────────────────────────────── */
      hasRole: (role: UserRole | UserRole[]) => {
        const userRole = get().user?.role;
        if (!userRole) return false;
        return Array.isArray(role) ? role.includes(userRole) : userRole === role;
      },

      hasPermission: (permission: Permission) => {
        const permissions = get().user?.permissions ?? [];
        return (
          permissions.includes(permission) ||
          // Superadmins bypass all permission checks
          get().user?.role === "superadmin"
        );
      },

      isAuthenticated: () => {
        const { user, token } = get();
        return !!user && !!token;
      },
    }),

    {
      name: "edubest-auth",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : sessionStorage,
      ),
      // Only persist the user object and tenant — not loading flags
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        tenant: state.tenant,
      }),
    },
  ),
);
