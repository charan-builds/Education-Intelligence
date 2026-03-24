"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bell, ChevronLeft, ChevronRight, Command, LogOut, Menu, Search, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PropsWithChildren, useMemo, useState } from "react";

import ThemeToggle from "@/components/ui/ThemeToggle";
import RequireRole from "@/components/auth/RequireRole";
import { useAuth } from "@/hooks/useAuth";
import { useTenant } from "@/hooks/useTenant";
import { AppNavItem, matchNavItem } from "@/components/layouts/navigation";
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

  return (
    <div className="flex h-full flex-col">
      <div className="rounded-[30px] border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(15,23,42,0.82))] p-4 text-white shadow-glow">
        <div className="flex items-center gap-3">
          <Logo
            showWordmark={!condensed}
            labelClassName="text-white [&>p:first-child]:text-teal-200 [&>p:last-child]:text-white"
          />
          {!condensed ? (
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-indigo-200">{roleLabel}</p>
              <p className="mt-1 text-xs text-slate-400">Adaptive learning intelligence workspace</p>
            </div>
          ) : null}
        </div>
      </div>

      <nav className="mt-6 space-y-2">
        {navigation.map((item) => {
          const active = matchNavItem(pathname, item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "group flex items-center gap-3 rounded-[20px] px-3 py-3 text-sm font-medium transition",
                active
                  ? "bg-white text-slate-950 shadow-panel"
                  : "text-slate-300 hover:bg-white/8 hover:text-white",
              )}
            >
              <item.icon className={cn("h-5 w-5 flex-none", active ? "text-brand-700" : "text-slate-400 group-hover:text-white")} />
              {!condensed ? <span>{item.label}</span> : null}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-[30px] border border-white/10 bg-white/5 p-4 text-slate-200">
        {!condensed ? (
          <>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Session</p>
            <p className="mt-3 text-sm font-semibold">User #{user?.user_id ?? "?"}</p>
            <p className="mt-1 text-sm capitalize text-slate-400">{user?.role?.replace("_", " ") ?? "Guest"}</p>
            <p className="mt-1 text-sm text-slate-400">Tenant #{user?.tenant_id ?? "?"}</p>
            {activeTenantScope ? (
              <button
                type="button"
                onClick={clearActiveTenantScope}
                className="mt-4 w-full rounded-2xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-left text-xs font-semibold uppercase tracking-[0.18em] text-amber-100 transition hover:bg-amber-400/15"
              >
                Inspecting tenant #{activeTenantScope}
              </button>
            ) : null}
          </>
        ) : null}
        <button
          type="button"
          onClick={logout}
          className={cn(
            "mt-4 inline-flex items-center gap-2 rounded-2xl border border-white/10 px-3 py-2 text-sm font-semibold transition hover:bg-white/10",
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

  const activeSection = useMemo(
    () => navigation.find((item) => matchNavItem(pathname, item))?.label ?? roleLabel,
    [navigation, pathname, roleLabel],
  );

  return (
    <RequireRole allowedRoles={allowedRoles}>
      <div className="app-shell relative">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.16),_transparent_26%),radial-gradient(circle_at_80%_20%,_rgba(14,165,145,0.1),_transparent_22%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.08),_transparent_24%)]" />

        <div className="flex min-h-screen">
          <aside
            className={cn(
              "hidden shrink-0 border-r border-white/10 bg-[linear-gradient(180deg,rgba(2,6,23,0.98),rgba(15,23,42,0.9))] px-4 py-5 text-white backdrop-blur-xl lg:block",
              condensed ? "w-24" : "w-80",
            )}
          >
            <div className="mb-4 flex justify-end">
              <button
                type="button"
                onClick={() => setCondensed((value) => !value)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5 transition hover:bg-white/10"
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
                  className="fixed inset-0 z-40 bg-slate-950/55 lg:hidden"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => setSidebarOpen(false)}
                />
                <motion.aside
                  className="fixed inset-y-0 left-0 z-50 w-80 bg-slate-950 px-4 py-5 text-white shadow-2xl lg:hidden"
                  initial={{ x: -24, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: -24, opacity: 0 }}
                >
                  <div className="mb-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setSidebarOpen(false)}
                      className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5"
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
            <div className="glass-surface soft-ring sticky top-4 z-30 flex items-center gap-3 rounded-[30px] px-4 py-3 dark:border-slate-700">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white/70 lg:hidden dark:border-slate-700 dark:bg-slate-900/80"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="relative min-w-0 flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  className="w-full rounded-[20px] border border-slate-200/90 bg-white/85 py-3 pl-11 pr-4 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-4 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 dark:focus:ring-brand-900/40"
                  placeholder={searchPlaceholder}
                />
              </div>
              <div className="hidden items-center gap-2 rounded-[20px] border border-slate-200 bg-white/80 px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 lg:flex dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-300">
                <Command className="h-3.5 w-3.5" />
                Search
              </div>
              <ThemeToggle />
              <div className="hidden items-center gap-2 rounded-[20px] border border-slate-200 bg-white/80 px-4 py-2 text-sm text-slate-600 md:flex dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-300">
                <Bell className="h-4 w-4 text-brand-600" />
                <span>{activeSection}</span>
              </div>
              <div className="rounded-[20px] border border-slate-200 bg-white/80 px-4 py-2 text-right dark:border-slate-700 dark:bg-slate-900/80">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Active</p>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {user?.role?.replace("_", " ") ?? roleLabel}
                </p>
              </div>
            </div>

            <main className="mx-auto mt-6 max-w-[1440px]">{children}</main>
          </div>
        </div>
      </div>
    </RequireRole>
  );
}
