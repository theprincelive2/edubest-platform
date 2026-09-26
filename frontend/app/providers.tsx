"use client";

/**
 * App-wide Provider Tree
 *
 * Extracted from layout.tsx into its own client component so that
 * the root layout can remain a Server Component (important for metadata
 * and font loading) while providers — which require client-side hooks
 * like useState — live in this separate file.
 */

import { useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";

interface ProvidersProps {
  children: React.ReactNode;
}

/**
 * Creates a stable QueryClient instance per render cycle.
 *
 * Configuration decisions:
 *  - staleTime: 60 s — most school data doesn't change by the second
 *  - retry: 1 — avoid hammering the backend on network hiccups
 *  - refetchOnWindowFocus: false — prevents noisy refetches in school labs
 *    where users switch tabs frequently
 */
function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,        // 60 seconds
        gcTime: 10 * 60 * 1000,      // 10 minutes garbage collection
        retry: 1,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined;

function getQueryClient(): QueryClient {
  if (typeof window === "undefined") {
    // Server: always create a new client
    return makeQueryClient();
  }
  // Browser: reuse the same client instance across hot reloads
  if (!browserQueryClient) browserQueryClient = makeQueryClient();
  return browserQueryClient;
}

export function Providers({ children }: ProvidersProps) {
  // useState ensures a stable client on the initial render
  const [queryClient] = useState(getQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="light"
        enableSystem
        disableTransitionOnChange
      >
        {children}

        {/* Toast notification system — rendered at document root */}
        <Toaster
          position="top-right"
          richColors
          closeButton
          duration={4000}
          toastOptions={{
            classNames: {
              toast: "font-sans",
            },
          }}
        />
      </ThemeProvider>

      {/* Dev-only query inspector — stripped from production builds */}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
