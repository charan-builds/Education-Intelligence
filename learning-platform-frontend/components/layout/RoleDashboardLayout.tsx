"use client";

import Link from "next/link";
import React, { ReactNode } from "react";

import { useAuth } from "@/hooks/useAuth";
import { useTenantScope } from "@/hooks/useTenantScope";

export type DashboardNavItem = {
  label: string;
  href: string;
};

export type DashboardBreadcrumbItem = {
  label: string;
  href?: string;
};

type RoleDashboardLayoutProps = {
  roleLabel: string;
  title: string;
  description: string;
  navItems: DashboardNavItem[];
  breadcrumbs?: DashboardBreadcrumbItem[];
  actions?: ReactNode;
  children: ReactNode;
};

export default function RoleDashboardLayout({
  roleLabel,
  title,
  description,
  navItems,
  breadcrumbs,
  actions,
  children,
}: RoleDashboardLayoutProps) {
  const { user, logout } = useAuth();
  const { activeTenantScope, clearActiveTenantScope } = useTenantScope();

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#e2e8f0_100%)]">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 gap-0 lg:grid-cols-[260px_1fr]">
        <aside className="border-r border-slate-200 bg-slate-950 px-5 py-8 text-slate-100">
          <div className="rounded-3xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-sky-300">{roleLabel}</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">LearnIQ Ops</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Unified frontend connected to your FastAPI backend.</p>
          </div>

          <nav className="mt-6 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-2xl px-4 py-3 text-sm font-medium text-slate-300 transition hover:bg-slate-900 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="mt-8 rounded-3xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Session</p>
            <p className="mt-3 text-sm text-slate-300">User #{user?.user_id ?? "-"}</p>
            <p className="mt-1 text-sm text-slate-400">Tenant #{user?.tenant_id ?? "-"}</p>
            {user?.role === "super_admin" && activeTenantScope ? (
              <div className="mt-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">Inspection Scope</p>
                <p className="mt-2 text-sm text-amber-100">Viewing tenant #{activeTenantScope}</p>
                <button
                  type="button"
                  onClick={clearActiveTenantScope}
                  className="mt-3 w-full rounded-xl border border-amber-400/40 px-3 py-2 text-sm font-medium text-amber-100 transition hover:bg-amber-400/10"
                >
                  Clear Tenant Scope
                </button>
              </div>
            ) : null}
            <button
              type="button"
              onClick={logout}
              className="mt-4 w-full rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
            >
              Logout
            </button>
          </div>
        </aside>

        <div className="px-6 py-8 lg:px-8">
          <header className="rounded-[28px] border border-white/70 bg-white/90 p-6 shadow-lg">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-700">{roleLabel}</p>
                {user?.role === "super_admin" && activeTenantScope ? (
                  <div className="mt-3 inline-flex items-center rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
                    Inspection Tenant #{activeTenantScope}
                  </div>
                ) : null}
                {breadcrumbs && breadcrumbs.length > 0 ? (
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                    {breadcrumbs.map((item, index) => (
                      <React.Fragment key={`${item.label}-${index}`}>
                        {index > 0 ? <span className="text-slate-300">/</span> : null}
                        {item.href ? (
                          <Link href={item.href} className="transition hover:text-sky-700">
                            {item.label}
                          </Link>
                        ) : (
                          <span className="font-medium text-slate-700">{item.label}</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                ) : null}
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{title}</h1>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">{description}</p>
              </div>
              {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
            </div>
          </header>

          <main className="mt-6 space-y-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
