import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { TenantConfig, AcademicYear, Term, GradingScale } from "@/types";

/**
 * Edubest Tenant Zustand Store
 *
 * Holds school / tenant context that is global and rarely changes.
 * Loaded once after login (or on page hydration) and referenced
 * throughout the app for:
 *  - Displaying the school name, logo, and branding
 *  - Knowing the current academic year and term for API queries
 *  - Applying the school's custom grading scale
 *  - Checking which features are enabled for this school
 *
 * The store is persisted to localStorage so that the UI doesn't flash
 * placeholder text on refresh — but always re-fetches in the background
 * to pick up any settings changes made by an admin.
 */

interface TenantState {
  /** Full tenant/school configuration object */
  tenantConfig: TenantConfig | null;

  /** Current active academic year */
  currentAcademicYear: AcademicYear | null;

  /** Current active term within the academic year */
  currentTerm: Term | null;

  /** Whether the tenant data has been loaded at least once */
  isLoaded: boolean;

  /** Tracks an in-progress fetch to avoid double-loading */
  isLoading: boolean;
}

interface TenantActions {
  /** Called after fetching /schools/current/ — replaces entire config */
  setTenantConfig: (config: TenantConfig) => void;

  /** Called after fetching /academic-years/?is_current=true */
  setCurrentAcademicYear: (year: AcademicYear) => void;

  /** Called after fetching /terms/?is_current=true */
  setCurrentTerm: (term: Term) => void;

  /** Partial update for school settings (e.g. after admin edits) */
  updateSchoolSettings: (updates: Partial<TenantConfig>) => void;

  /** Clears all tenant data — called on logout */
  clearTenant: () => void;

  setLoading: (loading: boolean) => void;

  /* ── Computed helpers ──────────────────────────────────────────── */

  /** Returns the school's name or a fallback placeholder string */
  getSchoolName: () => string;

  /** Returns the school's logo URL or null */
  getLogoUrl: () => string | null;

  /**
   * Looks up the letter grade for a given numeric score using
   * the school's custom grading scale.
   * Falls back to built-in scale if the school has not configured one.
   */
  getGradeForScore: (score: number) => GradingScale | null;

  /** Returns true if a given feature is enabled for this school */
  isFeatureEnabled: (
    feature: keyof TenantConfig["features"],
  ) => boolean;
}

type TenantStore = TenantState & TenantActions;

/* ── Default grading scale used when school has not set a custom one ── */
const DEFAULT_GRADING_SCALE: GradingScale[] = [
  { grade: "A+", min_score: 90, max_score: 100, remark: "Excellent" },
  { grade: "A",  min_score: 80, max_score: 89,  remark: "Very Good" },
  { grade: "B+", min_score: 75, max_score: 79,  remark: "Good" },
  { grade: "B",  min_score: 70, max_score: 74,  remark: "Credit" },
  { grade: "C+", min_score: 65, max_score: 69,  remark: "Average" },
  { grade: "C",  min_score: 60, max_score: 64,  remark: "Pass" },
  { grade: "D",  min_score: 50, max_score: 59,  remark: "Weak Pass" },
  { grade: "F",  min_score: 0,  max_score: 49,  remark: "Fail" },
];

/* ── Store ───────────────────────────────────────────────────────── */
export const useTenantStore = create<TenantStore>()(
  persist(
    (set, get) => ({
      /* ── Initial state ─────────────────────────────────────────── */
      tenantConfig: null,
      currentAcademicYear: null,
      currentTerm: null,
      isLoaded: false,
      isLoading: false,

      /* ── Actions ───────────────────────────────────────────────── */
      setTenantConfig: (config: TenantConfig) => {
        set({ tenantConfig: config, isLoaded: true, isLoading: false });
      },

      setCurrentAcademicYear: (year: AcademicYear) => {
        set({ currentAcademicYear: year });
      },

      setCurrentTerm: (term: Term) => {
        set({ currentTerm: term });
      },

      updateSchoolSettings: (updates: Partial<TenantConfig>) => {
        const current = get().tenantConfig;
        if (!current) return;
        set({ tenantConfig: { ...current, ...updates } });
      },

      clearTenant: () => {
        set({
          tenantConfig: null,
          currentAcademicYear: null,
          currentTerm: null,
          isLoaded: false,
        });
      },

      setLoading: (loading: boolean) => set({ isLoading: loading }),

      /* ── Computed helpers ───────────────────────────────────────── */
      getSchoolName: () => {
        return get().tenantConfig?.name ?? "Edubest School";
      },

      getLogoUrl: () => {
        return get().tenantConfig?.logo ?? null;
      },

      getGradeForScore: (score: number) => {
        const scale =
          get().tenantConfig?.grading_scale?.length
            ? get().tenantConfig!.grading_scale
            : DEFAULT_GRADING_SCALE;

        return (
          scale.find(
            (g) => score >= g.min_score && score <= g.max_score,
          ) ?? null
        );
      },

      isFeatureEnabled: (feature: keyof TenantConfig["features"]) => {
        return get().tenantConfig?.features?.[feature] ?? false;
      },
    }),

    {
      name: "edubest-tenant",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : sessionStorage,
      ),
      // Persist config and academic context but not loading flags
      partialize: (state) => ({
        tenantConfig: state.tenantConfig,
        currentAcademicYear: state.currentAcademicYear,
        currentTerm: state.currentTerm,
        isLoaded: state.isLoaded,
      }),
    },
  ),
);
