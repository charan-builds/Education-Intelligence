"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useState } from "react";

import { AuthProvider } from "@/components/providers/AuthProvider";
import DevAccessPanel from "@/components/dev/DevAccessPanel";
import { TenantProvider } from "@/components/providers/TenantProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { RealtimeProvider } from "@/components/providers/RealtimeProvider";
import { ToastProvider } from "@/components/providers/ToastProvider";
import PageTransition from "@/components/ui/PageTransition";

export default function Providers({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            gcTime: 5 * 60_000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 1,
          },
        },
      }),
  );

  const isLandingRoute = pathname === "/";

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TenantProvider>
            {isLandingRoute ? (
              children
            ) : (
              <ToastProvider>
                <RealtimeProvider>
                  <PageTransition>{children}</PageTransition>
                  <DevAccessPanel />
                </RealtimeProvider>
              </ToastProvider>
            )}
          </TenantProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
