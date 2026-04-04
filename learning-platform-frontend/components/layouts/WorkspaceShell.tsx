"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bell, ChevronLeft, ChevronRight, Command, LogOut, Menu, Search, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useMemo, useState } from "react";

import ThemeToggle from "@/components/ui/ThemeToggle";
import RequireRole from "@/components/auth/RequireRole";
import { useAuth } from "@/hooks/useAuth";
import { useTenant } from "@/hooks/useTenant";
import { AppNavItem, matchNavItem } from "@/components/layouts/navigation";
import { getWorkspaceRoleMeta } from "@/components/layouts/roleMeta";
import Logo from "@/components/brand/Logo";
import { cn } from "@/utils/cn";

type WorkspaceShellProps = PropsWithChildren<{
  allowedRoles: string[];
  roleLabel: string;
  navigation: AppNavItem[];
  searchPlaceholder?: string;
}>;

function SidebarContent({
  roleLabel,
  navigation,
  condensed,
  pathname,
  onNavigate,
}: {
  roleLabel: string;
  navigation: AppNavItem[];
  condensed: boolean;
  pathname: string;
  onNavigate?: () => void;
}) {
  const { user, logout } = useAuth();
  const { activeTenantScope, clearActiveTenantScope } = useTenant();
  const roleMeta = getWorkspaceRoleMeta(user?.role, roleLabel);

  return (
    <div className="flex h-full flex-col">
      <div className="rounded-[32px] border border-white/10 sidebar-glow p-5 text-white shadow-glow">
        <div className="flex items-center gap-3">
          <Logo
            showWordmark={!condensed}
            labelClassName="text-white [&>p:first-child]:text-violet-200 [&>p:last-child]:text-white"
          />
          {!condensed ? (
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-violet-200">{roleMeta.label}</p>
              <p className="mt-1 text-xs leading-5 text-violet-100/70">{roleMeta.headline}</p>
            </div>
          ) : null}
        </div>
      </div>

      <nav className="mt-6 space-y-2.5">
        {navigation.map((item) => {
          const active = matchNavItem(pathname, item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "group flex items-center gap-3 rounded-[22px] px-4 py-3.5 text-sm font-medium transition duration-300",
                active
                  ? "bg-white/14 text-white shadow-[0_20px_40px_rgba(76,29,149,0.28)] backdrop-blur"
                  : "text-violet-100/78 hover:bg-white/10 hover:text-white",
              )}
            >
              <item.icon
                className={cn("h-5 w-5 flex-none transition", active ? "text-violet-200" : "text-violet-200/60 group-hover:text-violet-100")}
              />
              {!condensed ? <span>{item.label}</span> : null}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-[30px] border border-white/10 bg-white/8 p-5 text-violet-100 backdrop-blur">
        {!condensed ? (
          <>
            <p className="text-xs uppercase tracking-[0.28em] text-violet-200/70">Session</p>
            <p className="mt-3 text-sm font-semibold">{user?.full_name ?? `User #${user?.user_id ?? "?"}`}</p>
            <p className="mt-1 text-sm text-violet-100/70">{user?.email ?? "Signed-in workspace session"}</p>
            <p className="mt-2 text-xs uppercase tracking-[0.18em] text-violet-200/70">{roleMeta.label}</p>
            <p className="mt-1 text-sm text-violet-100/70">Tenant #{user?.tenant_id ?? "?"}</p>
            {activeTenantScope ? (
              <button
                type="button"
                onClick={clearActiveTenantScope}
                className="mt-4 w-full rounded-2xl border border-violet-300/30 bg-violet-300/10 px-3 py-2 text-left text-xs font-semibold uppercase tracking-[0.18em] text-violet-100 transition hover:bg-violet-300/15"
              >
                Inspecting tenant #{activeTenantScope}
              </button>
            ) : null}
            <div className="mt-4 rounded-[20px] border border-white/10 bg-white/6 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-200/80">Guide</p>
              <p className="mt-2 text-sm leading-6 text-violet-100/72">{roleMeta.helper}</p>
            </div>
          </>
        ) : null}
        <button
          type="button"
          onClick={logout}
          className={cn(
            "mt-4 inline-flex items-center gap-2 rounded-2xl border border-white/10 px-3 py-2.5 text-sm font-semibold transition duration-300 hover:bg-white/10",
            condensed ? "w-full justify-center" : "w-full",
          )}
        >
          <LogOut className="h-4 w-4" />
          {!condensed ? "Logout" : null}
        </button>
      </div>
    </div>
  );
}

export default function WorkspaceShell({
  allowedRoles,
  roleLabel,
  navigation,
  searchPlaceholder = "Search learning data, topics, and activity",
  children,
}: WorkspaceShellProps) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [condensed, setCondensed] = useState(false);
  const { user } = useAuth();
  const roleMeta = getWorkspaceRoleMeta(user?.role, roleLabel);

  const activeSection = useMemo(
    () => navigation.find((item) => matchNavItem(pathname, item))?.label ?? roleLabel,
    [navigation, pathname, roleLabel],
  );
  const insightBadge = useMemo(() => {
    if (user?.role === "super_admin") {
      return "Tenant health and system analytics";
    }
    if (user?.role === "admin") {
      return "Institution analytics and user operations";
    }
    if (user?.role === "teacher" || user?.role === "mentor") {
      return "Learner support and performance tracking";
    }
    return "Roadmap guidance and progress insights";
  }, [user?.role]);

  return (
    <RequireRole allowedRoles={allowedRoles}>
      <div className="app-shell workspace-theme relative overflow-hidden">
        <div className="absolute inset-0 -z-10 workspace-surface" />
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(rgba(167,139,250,0.10)_1px,transparent_1px),linear-gradient(90deg,rgba(167,139,250,0.10)_1px,transparent_1px)] bg-[size:30px_30px] opacity-35" />
        <div className="absolute left-12 top-16 -z-10 h-72 w-72 rounded-full bg-violet-300/20 blur-[120px]" />
        <div className="absolute bottom-0 right-8 -z-10 h-80 w-80 rounded-full bg-fuchsia-200/20 blur-[140px]" />

        <div className="flex min-h-screen">
          <aside
            className={cn(
              "hidden shrink-0 border-r border-violet-950/20 sidebar-glow px-4 py-5 text-white backdrop-blur-xl lg:block",
              condensed ? "w-24" : "w-80",
            )}
          >
            <div className="mb-4 flex justify-end">
              <button
                type="button"
                onClick={() => setCondensed((value) => !value)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/6 transition duration-300 hover:bg-white/12"
                aria-label="Toggle sidebar"
              >
                {condensed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
              </button>
            </div>
            <SidebarContent roleLabel={roleLabel} navigation={navigation} condensed={condensed} pathname={pathname} />
          </aside>

          <AnimatePresence>
            {sidebarOpen ? (
              <>
                <motion.div
                  className="fixed inset-0 z-40 bg-violet-950/45 backdrop-blur-sm lg:hidden"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => setSidebarOpen(false)}
                />
                <motion.aside
                  className="fixed inset-y-0 left-0 z-50 w-80 sidebar-glow px-4 py-5 text-white shadow-2xl lg:hidden"
                  initial={{ x: -24, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: -24, opacity: 0 }}
                >
                  <div className="mb-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setSidebarOpen(false)}
                      className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/6"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <SidebarContent
                    roleLabel={roleLabel}
                    navigation={navigation}
                    condensed={false}
                    pathname={pathname}
                    onNavigate={() => setSidebarOpen(false)}
                  />
                </motion.aside>
              </>
            ) : null}
          </AnimatePresence>

          <div className="min-w-0 flex-1 px-4 py-4 md:px-6 lg:px-8">
            <div className="glass-surface soft-ring sticky top-4 z-30 flex flex-wrap items-center gap-3 rounded-[30px] px-4 py-3 md:flex-nowrap md:px-5 dark:border-violet-700/50">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-violet-200/70 bg-white/70 lg:hidden dark:border-violet-700 dark:bg-violet-950/70"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="relative min-w-0 flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-violet-400" />
                <input
                  type="search"
                  className="field-control rounded-[20px] py-3 pl-11 pr-4"
                  placeholder={searchPlaceholder}
                />
              </div>
              <div className="hidden items-center gap-2 rounded-[20px] border border-violet-200/80 bg-white/80 px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-violet-500 lg:flex dark:border-violet-700 dark:bg-violet-950/70 dark:text-violet-200">
                <Command className="h-3.5 w-3.5" />
                Search
              </div>
              <ThemeToggle />
              <div className="hidden items-center gap-2 rounded-[20px] border border-violet-200/80 bg-white/80 px-4 py-2 text-sm text-violet-700 md:flex dark:border-violet-700 dark:bg-violet-950/70 dark:text-violet-200">
                <Bell className="h-4 w-4 text-violet-600" />
                <span>{activeSection}</span>
              </div>
              <div className="hidden items-center gap-2 rounded-[20px] border border-violet-200/80 bg-violet-50/80 px-4 py-2 text-sm text-violet-700 xl:flex dark:border-violet-700 dark:bg-violet-900/40 dark:text-violet-100">
                <Sparkles className="h-4 w-4 text-violet-500" />
                <span>{insightBadge}</span>
              </div>
              <div className="rounded-[20px] border border-violet-200/80 bg-white/82 px-4 py-2 text-right dark:border-violet-700 dark:bg-violet-950/70">
                <p className="text-xs uppercase tracking-[0.24em] text-violet-400">Workspace</p>
                <p className="text-sm font-semibold text-violet-950 dark:text-violet-100">{roleMeta.label}</p>
              </div>
            </div>

            <section className="mx-auto mt-6 flex max-w-[1440px] flex-col gap-4 md:mt-8">
              <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
                <div className="glass-surface soft-ring rounded-[28px] px-5 py-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-500">{roleMeta.label}</p>
                      <h1 className="mt-2 text-2xl font-semibold tracking-tight text-violet-950 dark:text-violet-50">{roleMeta.headline}</h1>
                      <p className="mt-2 max-w-3xl text-sm leading-7 text-violet-800/78 dark:text-violet-100/74">{roleMeta.helper}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <div className="rounded-full border border-violet-200/80 bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-violet-600 dark:border-violet-700 dark:bg-violet-950/70 dark:text-violet-200">
                        {activeSection}
                      </div>
                      <div className="rounded-full border border-violet-200/80 bg-violet-50/85 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-violet-700 dark:border-violet-700 dark:bg-violet-900/40 dark:text-violet-100">
                        Tenant {user?.tenant_id ?? "current"}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="glass-surface soft-ring rounded-[28px] px-5 py-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-500">Quick guide</p>
                      <p className="mt-2 text-sm font-semibold text-violet-950 dark:text-violet-50">{user?.full_name ?? roleMeta.label}</p>
                      <p className="mt-1 text-sm leading-6 text-violet-800/78 dark:text-violet-100/74">{insightBadge}</p>
                    </div>
                    <div className="rounded-2xl bg-violet-100 p-3 text-violet-700 dark:bg-violet-500/10 dark:text-violet-100">
                      <Sparkles className="h-5 w-5" />
                    </div>
                  </div>
                </div>
              </div>

              <main className="pb-8">{children}</main>
            </section>
          </div>
        </div>
      </div>
    </RequireRole>
  );
}
