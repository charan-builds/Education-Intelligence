"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Award, Brain, Clock3, Sparkles, Target, Users } from "lucide-react";

import {
  dashboardActivity,
  dashboardPerformance,
  dashboardPreviewCourses,
  dashboardSkills,
  dashboardStats,
} from "@/components/landing-new/content";
import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";

export default function LandingDashboardPreview() {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <section className="relative py-28">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="Live Analytics"
          title="Dashboards that"
          accent="tell stories"
          description="The homepage now previews the product experience without interfering with the real dashboard routes."
          icon={Brain}
        />

        <div className="mt-16 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-[2rem] border-2 border-slate-200 bg-white/80 p-8 shadow-2xl backdrop-blur-xl md:col-span-2 xl:row-span-2">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-slate-900">Performance Trend</h3>
                <p className="text-sm text-slate-600">Last 6 months progression</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 shadow-lg">
                <Target className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="h-[280px]">
              {isMounted ? (
                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={280}>
                  <AreaChart data={dashboardPerformance}>
                    <defs>
                      <linearGradient id="landingScoreGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.32} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#E5E7EB" strokeDasharray="3 3" />
                    <XAxis dataKey="month" stroke="#64748B" />
                    <YAxis stroke="#64748B" />
                    <Tooltip contentStyle={{ borderRadius: 16, border: "1px solid #E2E8F0" }} />
                    <Area dataKey="score" type="monotone" stroke="#2563EB" strokeWidth={3} fill="url(#landingScoreGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full rounded-[1.5rem] bg-gradient-to-br from-sky-50 to-indigo-50" />
              )}
            </div>
            <div className="mt-5 grid grid-cols-3 gap-4">
              {dashboardStats.map((stat) => (
                <div key={stat.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="text-xs font-medium text-slate-500">{stat.label}</div>
                  <div className={`mt-1 text-xl font-bold ${stat.accentClassName}`}>{stat.value}</div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[2rem] border-2 border-yellow-300 bg-gradient-to-br from-yellow-100 to-amber-100 p-6 shadow-xl">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-yellow-400 to-amber-500 shadow-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <h3 className="mt-5 text-xl font-bold text-slate-900">AI Insights</h3>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              Learning velocity increased by 23% this week. Calculus remains the highest-confidence intervention.
            </p>
            <div className="mt-6 flex items-center gap-2 text-xs font-semibold text-slate-700">
              {[0, 1, 2].map((dot) => (
                <span key={dot} className="h-2 w-2 rounded-full bg-yellow-600" />
              ))}
              Analyzing live signals
            </div>
          </article>

          <article className="rounded-[2rem] border-2 border-slate-200 bg-white/80 p-6 shadow-xl backdrop-blur-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900">Weekly Activity</h3>
              <Clock3 className="h-5 w-5 text-slate-500" />
            </div>
            <div className="h-[140px]">
              {isMounted ? (
                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={140}>
                  <BarChart data={dashboardActivity}>
                    <XAxis dataKey="day" stroke="#64748B" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ borderRadius: 16, border: "1px solid #E2E8F0" }} />
                    <Bar dataKey="hours" fill="#FBBF24" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full rounded-[1.5rem] bg-gradient-to-br from-yellow-50 to-amber-50" />
              )}
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-slate-900">25.2h</div>
                <div className="text-xs text-slate-500">This week</div>
              </div>
              <div className="rounded-lg border border-emerald-300 bg-emerald-100 px-3 py-1 text-sm font-bold text-emerald-700">+18%</div>
            </div>
          </article>

          <article className="rounded-[2rem] border-2 border-slate-200 bg-white/80 p-6 shadow-xl backdrop-blur-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900">Skills</h3>
              <Target className="h-5 w-5 text-slate-500" />
            </div>
            <div className="h-[150px]">
              {isMounted ? (
                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={150}>
                  <PieChart>
                    <Pie data={dashboardSkills} dataKey="value" cx="50%" cy="50%" innerRadius={35} outerRadius={58} paddingAngle={5}>
                      {dashboardSkills.map((skill) => (
                        <Cell key={skill.name} fill={skill.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 16, border: "1px solid #E2E8F0" }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full rounded-full bg-gradient-to-br from-fuchsia-50 to-rose-50" />
              )}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {dashboardSkills.map((skill) => (
                <div key={skill.name} className="flex items-center gap-2 text-xs font-medium text-slate-700">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: skill.color }} />
                  {skill.name}
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[2rem] border-2 border-fuchsia-300 bg-gradient-to-br from-fuchsia-100 to-rose-100 p-6 shadow-xl">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 to-rose-600 shadow-lg">
              <Award className="h-8 w-8 text-white" />
            </div>
            <h3 className="mt-5 text-center text-xl font-bold text-slate-900">Top Performer</h3>
            <p className="mt-2 text-center text-sm leading-7 text-slate-700">You&apos;re in the top 5% of learners this month.</p>
            <div className="mt-4 rounded-xl border border-fuchsia-200 bg-white/80 p-4 text-center">
              <div className="text-2xl font-bold text-fuchsia-600">127</div>
              <div className="text-xs text-slate-500">Achievement points</div>
            </div>
          </article>

          <article className="rounded-[2rem] border-2 border-slate-200 bg-white/80 p-6 shadow-xl backdrop-blur-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900">Live Now</h3>
              <div className="inline-flex items-center gap-2 text-xs font-semibold text-rose-600">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                LIVE
              </div>
            </div>
            <div className="space-y-3">
              {dashboardPreviewCourses.map((course) => (
                <div key={course.title} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-900">{course.title}</span>
                    <Users className="h-4 w-4 text-slate-500" />
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="flex -space-x-1">
                      {[0, 1, 2].map((avatarIndex) => (
                        <div
                          key={avatarIndex}
                          className={`h-6 w-6 rounded-full border-2 border-white bg-gradient-to-br ${course.gradientClassName}`}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-slate-600">+{course.activeUsers} active</span>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
