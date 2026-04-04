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
  const roleName = user?.role?.replace("_", " ") ?? roleLabel;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.18),_transparent_20%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.14),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.12),_transparent_28%),linear-gradient(180deg,_#f6f8fc_0%,_#ffffff_100%)]">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 gap-0 lg:grid-cols-[280px_1fr]">
        <aside className="sidebar-glow border-r border-slate-900/8 px-5 py-8 text-white">
          <div className="rounded-[30px] border border-white/12 bg-white/10 p-5 backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-100">{roleLabel}</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Learnova Workspace</h2>
            <p className="mt-2 text-sm leading-6 text-slate-100/82">Role-aware product operations for a multi-tenant learning platform.</p>
          </div>

          <nav className="mt-6 space-y-2.5">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-[20px] border border-transparent px-4 py-3 text-sm font-medium text-slate-100/88 transition duration-300 hover:border-white/10 hover:bg-white/12 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="mt-8 rounded-[28px] border border-white/10 bg-white/8 p-4 backdrop-blur">
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/75">Session</p>
            <p className="mt-3 text-sm font-semibold text-white">User #{user?.user_id ?? "-"}</p>
            <p className="mt-1 text-sm capitalize text-slate-100/80">{roleName}</p>
            <p className="mt-1 text-sm text-slate-100/80">Tenant #{user?.tenant_id ?? "-"}</p>
            {user?.role === "super_admin" && activeTenantScope ? (
              <div className="mt-4 rounded-[20px] border border-violet-300/25 bg-violet-300/10 p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-100">Inspection Scope</p>
                  <p className="mt-2 text-sm text-violet-50">Viewing tenant #{activeTenantScope}</p>
                <button
                  type="button"
                  onClick={clearActiveTenantScope}
                  className="mt-3 w-full rounded-2xl border border-violet-300/25 px-3 py-2 text-sm font-medium text-violet-50 transition hover:bg-violet-300/10"
                >
                  Clear Tenant Scope
                </button>
              </div>
            ) : null}
            <button
              type="button"
              onClick={logout}
              className="mt-4 w-full rounded-2xl border border-white/10 px-4 py-2.5 text-sm font-semibold text-violet-50 transition hover:bg-white/10"
            >
              Logout
            </button>
          </div>
        </aside>

        <div className="px-6 py-8 lg:px-8">
          <header className="rounded-[30px] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] p-6 shadow-[0_28px_70px_-38px_rgba(15,23,42,0.22)] backdrop-blur">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-700">{roleLabel}</p>
                {user?.role === "super_admin" && activeTenantScope ? (
                  <div className="mt-3 inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
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
                          <span className="font-medium text-slate-900">{item.label}</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                ) : null}
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{title}</h1>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">{description}</p>
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
