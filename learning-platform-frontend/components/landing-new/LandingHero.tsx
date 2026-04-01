import { ArrowRight, Brain, LayoutDashboard, PlayCircle } from "lucide-react";
import Link from "next/link";

import { heroStats } from "@/components/landing-new/content";

type LandingHeroProps = {
  dashboardHref: string;
  isAuthenticated: boolean;
};

export default function LandingHero({ dashboardHref, isAuthenticated }: LandingHeroProps) {
  return (
    <section className="relative overflow-hidden pb-28 pt-28 sm:pb-32 sm:pt-36">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-10 h-[420px] w-[420px] rounded-full bg-yellow-300/30 blur-[130px]" />
        <div className="absolute bottom-[-10%] right-[-5%] h-[520px] w-[520px] rounded-full bg-amber-300/25 blur-[150px]" />
      </div>

      <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border-2 border-yellow-200 bg-white/80 px-4 py-2 shadow-lg backdrop-blur-xl">
            <Brain className="h-4 w-4 text-yellow-600" />
            <span className="text-sm font-semibold text-slate-900">Powered by Advanced AI</span>
            <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">LIVE</span>
          </div>

          <h1 className="mt-8 max-w-3xl text-5xl font-bold leading-[1.05] tracking-tight text-slate-950 sm:text-6xl lg:text-7xl">
            Turn learning into <span className="bg-gradient-to-r from-yellow-500 via-amber-500 to-orange-500 bg-clip-text text-transparent">intelligence</span>
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 sm:text-xl">
            AI-powered diagnostics uncover learning gaps, generate personalized roadmaps, and connect students, teachers,
            and institutions through one premium workspace.
          </p>

          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:flex-wrap">
            {isAuthenticated ? (
              <Link
                href={dashboardHref}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-8 py-4 text-base font-semibold text-white shadow-2xl shadow-slate-950/15 transition hover:-translate-y-0.5 hover:bg-slate-900"
              >
                <LayoutDashboard className="h-5 w-5" />
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/auth?mode=register"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-yellow-400 to-amber-500 px-8 py-4 text-base font-semibold text-white shadow-2xl shadow-yellow-500/25 transition hover:-translate-y-0.5 hover:from-yellow-500 hover:to-amber-600"
                >
                  Get Started
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  href="/auth?mode=login"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border-2 border-slate-200 bg-white px-8 py-4 text-base font-semibold text-slate-900 shadow-xl transition hover:-translate-y-0.5 hover:bg-slate-50"
                >
                  <PlayCircle className="h-5 w-5 text-yellow-600" />
                  Login
                </Link>
              </>
            )}
          </div>

          <div className="mt-12 flex flex-wrap gap-8 border-t border-slate-200 pt-8">
            {heroStats.map((stat) => (
              <div key={stat.label}>
                <div className={`text-3xl font-bold ${stat.accentClassName}`}>{stat.value}</div>
                <div className="mt-1 text-sm font-medium text-slate-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative hidden sm:block">
          <div className="rounded-[2rem] border-2 border-slate-200/80 bg-white/75 p-6 shadow-2xl backdrop-blur-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-yellow-400 to-amber-500 shadow-md">
                  <Brain className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">Learning Dashboard</h2>
                  <p className="text-xs text-slate-600">Real-time insight panel</p>
                </div>
              </div>
              <div className="inline-flex items-center gap-2 rounded-xl border border-emerald-300 bg-emerald-100 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Live
              </div>
            </div>

            <div className="mt-6 space-y-4">
              {[
                { label: "Mathematics", progress: "85%", barClassName: "bg-sky-500" },
                { label: "Science", progress: "72%", barClassName: "bg-emerald-500" },
                { label: "Literature", progress: "91%", barClassName: "bg-fuchsia-500" },
              ].map((item) => (
                <div key={item.label}>
                  <div className="mb-2 flex items-center justify-between text-sm font-medium text-slate-800">
                    <span>{item.label}</span>
                    <span>{item.progress}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200">
                    <div className={`h-2 rounded-full ${item.barClassName}`} style={{ width: item.progress }} />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-[1.5rem] border-2 border-yellow-300 bg-gradient-to-br from-yellow-100 to-amber-100 p-4">
              <div className="flex gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-yellow-400">
                  <Brain className="h-4 w-4 text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">AI recommendation</h3>
                  <p className="mt-1 text-xs leading-6 text-slate-700">
                    Focus on calculus derivatives next. Current pattern analysis shows 23% improvement potential.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="absolute -right-4 -top-6 w-44 rounded-[1.4rem] border-2 border-emerald-200 bg-white/85 p-4 shadow-xl backdrop-blur-xl">
            <div className="text-xs font-semibold text-slate-600">Growth Rate</div>
            <div className="mt-1 text-3xl font-bold text-emerald-600">+127%</div>
            <div className="text-xs text-slate-500">This semester</div>
          </div>

          <div className="absolute -bottom-6 -left-6 w-48 rounded-[1.4rem] border-2 border-sky-200 bg-white/85 p-4 shadow-xl backdrop-blur-xl">
            <div className="text-xs font-semibold text-slate-600">Active Sessions</div>
            <div className="mt-3 flex items-center gap-3">
              <div className="flex -space-x-2">
                {["A", "B", "C"].map((label) => (
                  <div
                    key={label}
                    className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-gradient-to-br from-sky-400 to-indigo-500 text-xs font-bold text-white"
                  >
                    {label}
                  </div>
                ))}
              </div>
              <div className="text-sm font-bold text-slate-900">+2,458</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
