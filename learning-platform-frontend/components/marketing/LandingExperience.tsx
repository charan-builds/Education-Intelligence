"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  Bell,
  Bot,
  BrainCircuit,
  Building2,
  CheckCircle2,
  CircleAlert,
  Command,
  Compass,
  GraduationCap,
  Keyboard,
  LineChart,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Users2,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart as RechartsLineChart,
  RadialBar,
  RadialBarChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import ThemeToggle from "@/components/ui/ThemeToggle";
import { appRoutes } from "@/utils/appRoutes";
import { cn } from "@/utils/cn";

const heroStats = [
  { label: "Mastery lift", value: "+31%", detail: "after AI sequencing reprioritized weak-topic pressure" },
  { label: "Signals modeled", value: "17", detail: "confidence, pace, retention, readiness, drift, and intent" },
  { label: "Mentor prep", value: "1 tap", detail: "live intervention brief before every high-risk session" },
];

const masteryData = [
  { day: "Mon", mastery: 44, forecast: 50 },
  { day: "Tue", mastery: 49, forecast: 55 },
  { day: "Wed", mastery: 54, forecast: 59 },
  { day: "Thu", mastery: 60, forecast: 63 },
  { day: "Fri", mastery: 68, forecast: 70 },
  { day: "Sat", mastery: 73, forecast: 76 },
  { day: "Sun", mastery: 81, forecast: 84 },
];

const progressStats = [
  { label: "Roadmap completion", value: "74%", tone: "text-emerald-300" },
  { label: "Weak topics reduced", value: "6", tone: "text-indigo-200" },
  { label: "Goal confidence", value: "92%", tone: "text-sky-200" },
];

const heatmapRows = [
  { topic: "Probability", values: [0.24, 0.42, 0.58, 0.72, 0.86] },
  { topic: "Linear Algebra", values: [0.3, 0.36, 0.48, 0.61, 0.74] },
  { topic: "Gradient Descent", values: [0.62, 0.84, 0.73, 0.5, 0.38] },
  { topic: "Model Tuning", values: [0.18, 0.26, 0.42, 0.56, 0.69] },
];

const roadmapSteps = [
  { title: "Rebuild gradient intuition", detail: "12 min concept sprint", stage: "Now", tint: "from-indigo-400 to-violet-300" },
  { title: "Target weak-topic drills", detail: "8 adaptive questions", stage: "Queued", tint: "from-sky-400 to-cyan-300" },
  { title: "Spaced recap checkpoint", detail: "Retention block after mastery jump", stage: "Next", tint: "from-emerald-400 to-teal-300" },
];

const activityFeedItems = [
  { title: "Diagnostic completed", meta: "09:12 UTC", detail: "17 learner signals captured across readiness, speed, and confidence.", tone: "bg-emerald-400" },
  { title: "Knowledge graph updated", meta: "09:15 UTC", detail: "AI detected prerequisite drag between vectors and optimization.", tone: "bg-indigo-400" },
  { title: "Mentor brief refreshed", meta: "Live", detail: "Intervention note recommends guided mode before introducing tuning.", tone: "bg-amber-400" },
];

const recommendations = [
  "Reduce breadth in tomorrow's session and stay inside one high-friction concept cluster.",
  "Keep the learner in guided mode until optimization confidence rises above 72%.",
  "Add a recap sprint after the next mastery jump to protect long-term retention.",
];

const notificationItems = [
  { title: "Mentor brief refreshed", detail: "Maya Chen crossed the intervention threshold", tone: "text-amber-300" },
  { title: "Goal confidence improved", detail: "Roadmap lift forecast moved from 84% to 92%", tone: "text-emerald-300" },
];

const commandItems = [
  { label: "Open learner profile", shortcut: "G P" },
  { label: "Generate roadmap", shortcut: "G R" },
  { label: "View intervention queue", shortcut: "G I" },
];

const avatarUsers = [
  { name: "MC", color: "from-indigo-400 to-violet-300" },
  { name: "AV", color: "from-emerald-400 to-teal-300" },
  { name: "NO", color: "from-sky-400 to-cyan-300" },
  { name: "+4", color: "from-slate-500 to-slate-400" },
];

const workflowSteps = [
  {
    title: "Take Diagnostic Test",
    detail: "Adaptive questions detect speed, certainty, gaps, and prerequisite readiness.",
    icon: Activity,
  },
  {
    title: "AI Analyzes Weakness",
    detail: "The system models weak-topic pressure and predicts where progress is likely to stall.",
    icon: BrainCircuit,
  },
  {
    title: "Roadmap Generated",
    detail: "The engine builds a personalized sequence of lessons, drills, and retention blocks.",
    icon: Compass,
  },
  {
    title: "Track Progress",
    detail: "Every session refreshes forecasts, progress metrics, and intervention timing.",
    icon: LineChart,
  },
  {
    title: "Achieve Goal",
    detail: "Learners move toward mastery with measurable momentum and mentor-backed support.",
    icon: Target,
  },
];

const teacherComparisonData = [
  { name: "Ava", mastery: 88, risk: 18 },
  { name: "Maya", mastery: 74, risk: 34 },
  { name: "Leo", mastery: 61, risk: 57 },
  { name: "Noah", mastery: 79, risk: 26 },
];

const adminAnalyticsData = [
  { month: "Jan", learners: 420, active: 318 },
  { month: "Feb", learners: 510, active: 404 },
  { month: "Mar", learners: 640, active: 528 },
  { month: "Apr", learners: 740, active: 612 },
];

const roleViews = [
  {
    key: "student",
    label: "Student View",
    title: "Adaptive roadmap with mastery feedback",
    description: "Learners see exactly what to study next, why it matters, and how each action changes their trajectory.",
  },
  {
    key: "teacher",
    label: "Teacher View",
    title: "Classroom performance with intervention alerts",
    description: "Teachers get comparison views, risk flags, and a clear map of which students need intervention now.",
  },
  {
    key: "admin",
    label: "Admin View",
    title: "Institution analytics across tenants and usage",
    description: "Admins monitor activation, growth, completion, and operational health at the institution level.",
  },
  {
    key: "mentor",
    label: "Mentor View",
    title: "AI-supported mentoring with live context",
    description: "Mentors get chat context, recommendation stacks, and intervention prompts informed by learner signals.",
  },
];

function GlassPanel({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(31,41,55,0.78),rgba(17,24,39,0.7))] backdrop-blur-2xl",
        "shadow-[0_18px_40px_rgba(2,6,23,0.3),0_28px_120px_rgba(2,6,23,0.42)] transition duration-300 ease-out will-change-transform",
        "before:pointer-events-none before:absolute before:inset-0 before:rounded-[32px] before:border before:border-[rgba(99,102,241,0.16)]",
        "after:pointer-events-none after:absolute after:inset-x-8 after:top-0 after:h-px after:bg-gradient-to-r after:from-transparent after:via-[rgba(129,140,248,0.72)] after:to-transparent",
        "hover:border-white/14 hover:shadow-[0_24px_60px_rgba(2,6,23,0.38),0_34px_140px_rgba(79,70,229,0.14)]",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.09),transparent_28%),radial-gradient(circle_at_bottom_left,rgba(34,211,238,0.05),transparent_26%)]" />
      {children}
    </div>
  );
}

function DashboardCard({
  title,
  eyebrow,
  action,
  className,
  children,
}: {
  title: string;
  eyebrow: string;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <GlassPanel className={cn("p-6 hover:-translate-y-1 hover:shadow-[0_34px_120px_rgba(99,102,241,0.18)]", className)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">{eyebrow}</p>
          <h3 className="mt-4 text-xl font-semibold tracking-[-0.03em] text-white">{title}</h3>
        </div>
        {action}
      </div>
      <div className="mt-6">{children}</div>
    </GlassPanel>
  );
}

function SectionEyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="inline-flex items-center rounded-full border border-[rgba(99,102,241,0.28)] bg-[rgba(99,102,241,0.12)] px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.32em] text-indigo-100 shadow-[0_0_30px_rgba(99,102,241,0.18)]">
      {children}
    </div>
  );
}

function UserAvatarStack() {
  return (
    <div className="flex items-center">
      {avatarUsers.map((user, index) => (
        <div
          key={user.name}
          className={cn(
            "relative -ml-2 first:ml-0 flex h-9 w-9 items-center justify-center rounded-full border border-[#0B1220] bg-gradient-to-br text-[11px] font-semibold text-white shadow-[0_8px_24px_rgba(2,6,23,0.35)]",
            user.color,
          )}
          style={{ zIndex: avatarUsers.length - index }}
        >
          {user.name}
        </div>
      ))}
    </div>
  );
}

function SmartSearchBar() {
  return (
    <div className="flex flex-1 items-center gap-3 rounded-2xl border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.03))] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] transition duration-300 hover:border-white/12 hover:bg-white/[0.06]">
      <Search className="h-4 w-4 text-slate-500" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-slate-200">Search learners, roadmaps, institutions, or AI commands</p>
      </div>
      <div className="hidden items-center gap-1 md:flex">
        <kbd className="rounded-md border border-white/10 bg-[#0F172A] px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-400">⌘</kbd>
        <kbd className="rounded-md border border-white/10 bg-[#0F172A] px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-400">K</kbd>
      </div>
    </div>
  );
}

function NotificationSystem() {
  return (
    <div className="rounded-2xl border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.03))] p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-indigo-200" />
          <p className="text-sm font-medium text-white">Notifications</p>
        </div>
        <div className="rounded-full border border-indigo-300/20 bg-indigo-400/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-indigo-100">
          02 New
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {notificationItems.map((item) => (
          <div key={item.title} className="rounded-xl border border-white/8 bg-[#0F172A]/72 px-3 py-2.5">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-white">{item.title}</p>
              <span className={cn("text-[11px] font-semibold uppercase tracking-[0.18em]", item.tone)}>Live</span>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-400">{item.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function CommandPalettePreview() {
  return (
    <GlassPanel className="p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Command palette</p>
          <h3 className="mt-4 text-xl font-semibold text-white">A keyboard-first system for fast operators</h3>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300">
          <Command className="h-3.5 w-3.5" />
          <span>⌘K</span>
        </div>
      </div>
      <div className="mt-6 rounded-[24px] border border-white/8 bg-[#0B1220]/76 p-4">
        <div className="flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3">
          <Search className="h-4 w-4 text-slate-500" />
          <span className="flex-1 text-sm text-slate-300">Jump to learner, roadmap, class alert, or AI action</span>
          <div className="hidden items-center gap-1 sm:flex">
            <kbd className="rounded-md border border-white/10 bg-[#111827] px-2 py-1 text-[10px] text-slate-400">⌘</kbd>
            <kbd className="rounded-md border border-white/10 bg-[#111827] px-2 py-1 text-[10px] text-slate-400">K</kbd>
          </div>
        </div>
        <div className="mt-4 space-y-3">
          {commandItems.map((item, index) => (
            <motion.div
              key={item.label}
              whileHover={{ x: 4 }}
              className={cn(
                "flex items-center justify-between rounded-2xl border px-3 py-3 transition duration-300",
                index === 0 ? "border-indigo-300/16 bg-indigo-400/10" : "border-white/8 bg-white/[0.035]",
              )}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-white/8 bg-[#111827] p-2 text-slate-300">
                  <Command className="h-4 w-4" />
                </div>
                <span className="text-sm text-white">{item.label}</span>
              </div>
              <span className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{item.shortcut}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </GlassPanel>
  );
}

function RippleButton({
  href,
  variant = "primary",
  children,
}: {
  href: string;
  variant?: "primary" | "secondary";
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group relative inline-flex items-center justify-center overflow-hidden rounded-2xl px-6 py-4 text-sm font-semibold transition duration-300 ease-out hover:-translate-y-0.5",
        variant === "primary"
          ? "border border-indigo-300/16 bg-[#6366F1] text-white hover:bg-[#7274ff] hover:shadow-[0_18px_50px_rgba(99,102,241,0.42)]"
          : "border border-white/12 bg-white/7 text-slate-100 hover:border-white/18 hover:bg-white/10",
      )}
    >
      <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition duration-500 group-hover:translate-x-full" />
      <span className="relative z-10 flex items-center gap-2">
        {children}
        <ArrowRight className="h-4 w-4 transition duration-300 group-hover:translate-x-1" />
      </span>
    </Link>
  );
}

function LoadingSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {[0, 1, 2].map((item) => (
        <div
          key={item}
          className="relative overflow-hidden rounded-2xl border border-white/8 bg-white/[0.04] p-4"
        >
          <div className="absolute inset-0 animate-[shimmer_2.2s_linear_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          <div className="relative space-y-3">
            <div className="h-2.5 w-16 rounded-full bg-white/10" />
            <div className="h-7 w-24 rounded-full bg-white/10" />
            <div className="h-2.5 w-full rounded-full bg-white/10" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyStateIllustration({
  title,
  note,
}: {
  title: string;
  note: string;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.025))] p-4">
      <div className="flex items-center gap-4">
        <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-[#0F172A]">
          <div className="absolute inset-3 rounded-full border border-indigo-300/20" />
          <div className="absolute inset-5 rounded-full bg-[rgba(99,102,241,0.22)] blur-sm" />
          <CheckCircle2 className="relative z-10 h-5 w-5 text-indigo-200" />
        </div>
        <div>
          <p className="text-base font-semibold text-white">{title}</p>
          <p className="mt-1 text-sm leading-6 text-slate-400">{note}</p>
        </div>
      </div>
    </div>
  );
}

function AnalyticsChart() {
  return (
    <DashboardCard
      eyebrow="Student Mastery Graph"
      title="Mastery climbs as the system re-sequences content in real time"
      action={<div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-100">+18% this week</div>}
    >
      <div className="rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(11,18,32,0.94),rgba(11,18,32,0.8))] p-4">
        <div className="mb-4 flex items-center justify-between text-xs text-slate-400">
          <span>Observed mastery</span>
          <span>Forecast confidence 92%</span>
        </div>
        <div className="overflow-hidden">
          <AreaChart width={520} height={208} data={masteryData} className="h-auto w-full">
            <defs>
              <linearGradient id="masteryArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366F1" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#6366F1" stopOpacity={0.03} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="day" tick={{ fill: "#64748B", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748B", fontSize: 11 }} axisLine={false} tickLine={false} domain={[35, 90]} />
            <Tooltip
              cursor={{ stroke: "rgba(99,102,241,0.25)" }}
              contentStyle={{
                background: "rgba(15,23,42,0.95)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "16px",
                color: "#E2E8F0",
              }}
            />
            <Area type="monotone" dataKey="mastery" stroke="#818CF8" strokeWidth={3} fill="url(#masteryArea)" />
            <Line type="monotone" dataKey="forecast" stroke="#22D3EE" strokeWidth={2} dot={false} strokeDasharray="4 4" />
          </AreaChart>
        </div>
      </div>
    </DashboardCard>
  );
}

function HeatmapGrid() {
  return (
    <DashboardCard
      eyebrow="Weak Topics Heatmap"
      title="Intensity increases where the learner is most likely to stall next"
      action={<div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">5-day drift</div>}
    >
      <div className="space-y-4">
        {heatmapRows.map((row) => (
          <div key={row.topic} className="grid grid-cols-[122px_1fr] items-center gap-3">
            <p className="text-sm font-medium text-slate-300">{row.topic}</p>
            <div className="grid grid-cols-5 gap-2">
              {row.values.map((value, index) => (
                <motion.div
                  key={`${row.topic}-${index}`}
                  whileHover={{ y: -3, scale: 1.05 }}
                  className="h-9 rounded-xl border border-white/8 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                  style={{
                    backgroundColor: `rgba(99,102,241,${value})`,
                    boxShadow: `0 0 22px rgba(99,102,241,${Math.max(0.12, value - 0.08)})`,
                  }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-5 flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs text-slate-300">
        <span>Darkest regions feed roadmap priority</span>
        <span className="text-indigo-200">AI reprioritizes automatically</span>
      </div>
    </DashboardCard>
  );
}

function RoadmapTimeline() {
  return (
    <DashboardCard
      eyebrow="AI-Generated Roadmap"
      title="The next session plan is generated around mastery lift, not static order"
      action={<div className="rounded-full border border-indigo-400/20 bg-indigo-400/10 px-3 py-1 text-xs font-semibold text-indigo-100">Generated in 1.2s</div>}
    >
      <div className="space-y-4">
        {roadmapSteps.map((step, index) => (
          <motion.div
            key={step.title}
            whileHover={{ y: -4, scale: 1.01 }}
            className="relative overflow-hidden rounded-[22px] border border-white/8 bg-[linear-gradient(180deg,rgba(15,23,42,0.88),rgba(15,23,42,0.72))] px-4 py-4 transition duration-300 hover:border-white/12"
          >
            <div className={cn("absolute inset-y-0 left-0 w-1 bg-gradient-to-b", step.tint)} />
            <div className="flex items-start justify-between gap-4 pl-3">
              <div>
                <p className="text-sm font-semibold text-white">{step.title}</p>
                <p className="mt-1 text-xs text-slate-400">{step.detail}</p>
              </div>
              <div className="text-right">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">Stage {index + 1}</p>
                <p className="mt-1 text-sm text-slate-200">{step.stage}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </DashboardCard>
  );
}

function ProgressRing({ value }: { value: number }) {
  return (
    <DashboardCard
      eyebrow="Progress Completion Stats"
      title="Live progress combines roadmap momentum, risk reduction, and confidence"
      className="h-full"
    >
        <div className="grid gap-6 md:grid-cols-[140px_1fr] md:items-center">
        <div className="overflow-hidden">
          <RadialBarChart
            width={140}
            height={140}
            innerRadius="72%"
            outerRadius="100%"
            data={[{ name: "progress", value, fill: "#6366F1" }]}
            startAngle={90}
            endAngle={-270}
          >
            <RadialBar dataKey="value" cornerRadius={20} background={{ fill: "rgba(255,255,255,0.08)" }} />
            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="fill-white text-2xl font-semibold">
              {value}%
            </text>
          </RadialBarChart>
        </div>
        <div className="grid gap-4">
          {progressStats.map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-slate-300">{item.label}</p>
                <p className={cn("text-sm font-semibold", item.tone)}>{item.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardCard>
  );
}

function ActivityFeed() {
  return (
    <DashboardCard eyebrow="Activity Feed" title="The system keeps producing visible work between learner sessions">
      <div className="space-y-4">
        {activityFeedItems.map((item) => (
          <motion.div
            key={item.title}
            whileHover={{ x: 4 }}
            className="rounded-[20px] border border-white/8 bg-white/[0.045] px-4 py-4 transition duration-300 hover:border-white/12 hover:bg-white/[0.06]"
          >
            <div className="flex items-start gap-3">
              <span className={cn("mt-1 h-2.5 w-2.5 rounded-full shadow-[0_0_16px_currentColor]", item.tone)} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-semibold text-white">{item.title}</p>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{item.meta}</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-300">{item.detail}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </DashboardCard>
  );
}

function AIRecommendationPanel({ floating = false }: { floating?: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.28, ease: "easeOut" }}
      className={cn(floating && "absolute -right-2 top-12 z-20 hidden w-[320px] xl:block")}
    >
      <DashboardCard
        eyebrow="AI Recommendations"
        title="Live mentor brief"
        action={<div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-100">Fresh</div>}
        className="border-[rgba(99,102,241,0.16)] bg-[rgba(15,23,42,0.82)] shadow-[0_26px_100px_rgba(2,6,23,0.55)]"
      >
        <div className="space-y-4">
          {recommendations.map((item) => (
            <motion.div
              key={item}
              whileHover={{ x: 4 }}
              className="rounded-[18px] border border-white/8 bg-gradient-to-r from-white/8 to-white/[0.03] px-4 py-4 text-sm leading-6 text-slate-200 transition duration-300 hover:border-white/12"
            >
              {item}
            </motion.div>
          ))}
        </div>
      </DashboardCard>
    </motion.div>
  );
}

function HeroDashboard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.1, ease: "easeOut" }}
      className="relative"
    >
      <div className="absolute -left-10 top-14 hidden h-44 w-44 rounded-full bg-[rgba(99,102,241,0.16)] blur-[100px] xl:block" />
      <div className="absolute -bottom-8 right-10 hidden h-48 w-48 rounded-full bg-[rgba(34,211,238,0.12)] blur-[120px] xl:block" />
      <AIRecommendationPanel floating />

      <GlassPanel className="landing-grid relative overflow-visible p-4 md:p-6">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-[rgba(99,102,241,0.08)] to-transparent" />
        <div className="pointer-events-none absolute inset-x-8 top-24 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        <div className="relative z-10 space-y-4 rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(11,18,32,0.92),rgba(11,18,32,0.86))] px-4 py-4 md:px-6 md:py-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Interactive dashboard preview</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-white">A live intelligence layer, not a static hero mock.</h2>
            </div>
            <div className="flex items-center gap-3">
              <UserAvatarStack />
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200">
                <span className="h-2 w-2 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.8)]" />
                Live system state
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <SmartSearchBar />
            <div className="flex items-center gap-3">
              <div className="rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-3 text-sm text-slate-300">
                <span className="font-medium text-white">Realtime:</span> 14 events synchronized
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-3 text-sm text-slate-300">
                <span className="font-medium text-white">Shortcut:</span> press <span className="text-indigo-200">⌘K</span>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 mt-4 rounded-[28px] border border-white/8 bg-[linear-gradient(180deg,rgba(11,18,32,0.82),rgba(11,18,32,0.72))] p-4 md:p-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/8 pb-4">
            <div>
              <p className="text-sm font-semibold text-white">Neural Calculus Pathway</p>
              <p className="mt-1 text-sm text-slate-400">Learner: Maya Chen • Session forecast: strong recovery</p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-slate-300">
              {["Mastery", "Weak Topics", "Roadmap", "Progress", "Activity"].map((pill, index) => (
                <div
                  key={pill}
                  className={cn(
                    "rounded-full border px-3 py-1.5 transition duration-300",
                    index === 0
                      ? "border-indigo-300/20 bg-indigo-400/12 text-indigo-100 shadow-[0_0_18px_rgba(99,102,241,0.2)]"
                      : "border-white/10 bg-white/5 hover:border-white/16 hover:bg-white/8",
                  )}
                >
                  {pill}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <div className="space-y-4">
              <AnalyticsChart />
              <div className="grid gap-4 md:grid-cols-2">
                <HeatmapGrid />
                <ProgressRing value={74} />
              </div>
            </div>
            <div className="space-y-4">
              <RoadmapTimeline />
              <ActivityFeed />
              <NotificationSystem />
            </div>
          </div>
        </div>
      </GlassPanel>
    </motion.div>
  );
}

function ProductFlowSection() {
  return (
    <section className="mt-32">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionEyebrow>Product flow</SectionEyebrow>
          <h2 className="mt-6 max-w-3xl text-3xl font-semibold tracking-[-0.04em] text-white md:text-5xl">
            From first signal to measurable mastery, every step is visible.
          </h2>
        </div>
        <p className="max-w-xl text-base leading-7 text-slate-300">
          The product story is operational, not abstract. Diagnostics create evidence, AI turns it into direction, and the platform keeps compounding signal into outcomes.
        </p>
      </div>

      <div className="relative mt-12 grid gap-4 lg:grid-cols-5">
        <div className="pointer-events-none absolute left-[10%] right-[10%] top-9 hidden h-px bg-gradient-to-r from-transparent via-[rgba(99,102,241,0.45)] to-transparent lg:block" />
        {workflowSteps.map((step, index) => {
          const Icon = step.icon;
          return (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.45, delay: index * 0.08 }}
            >
              <GlassPanel className="h-full min-h-[256px] p-6 hover:-translate-y-1 hover:shadow-[0_34px_120px_rgba(99,102,241,0.16)]">
                <motion.div
                  whileHover={{ scale: 1.04, rotate: -3 }}
                  className="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-[rgba(99,102,241,0.22)] bg-[rgba(99,102,241,0.14)] text-indigo-100 shadow-[0_0_24px_rgba(99,102,241,0.22)]"
                >
                  <Icon className="h-5 w-5" />
                </motion.div>
                <p className="mt-5 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Step 0{index + 1}</p>
                <h3 className="mt-3 text-xl font-semibold text-white">{step.title}</h3>
                <p className="mt-4 text-sm leading-7 text-slate-300">{step.detail}</p>
              </GlassPanel>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}

function StudentMiniDashboard() {
  return (
    <GlassPanel className="h-full p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Student View</p>
          <h3 className="mt-2 text-xl font-semibold text-white">Adaptive roadmap with mastery feedback</h3>
        </div>
        <GraduationCap className="h-5 w-5 text-indigo-200" />
      </div>
      <div className="mt-6 grid gap-4">
        <div className="rounded-2xl border border-white/8 bg-[#0B1220]/70 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-white">Mastery momentum</p>
            <span className="text-xs text-emerald-300">+9 this week</span>
          </div>
          <div className="overflow-hidden">
            <RechartsLineChart width={460} height={128} data={masteryData} className="h-auto w-full">
              <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
              <XAxis dataKey="day" tick={{ fill: "#64748B", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis hide domain={[35, 90]} />
              <Line type="monotone" dataKey="mastery" stroke="#6366F1" strokeWidth={3} dot={false} />
            </RechartsLineChart>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-white/8 bg-white/[0.045] p-4">
            <p className="text-sm font-medium text-white">Weak topics</p>
            <div className="mt-3 space-y-2">
              {["Gradient Descent", "Probability", "Model Tuning"].map((item, index) => (
                <div key={item} className="flex items-center justify-between rounded-xl bg-white/[0.04] px-3 py-2">
                  <span className="text-sm text-slate-300">{item}</span>
                  <span className="text-xs text-slate-400">{[84, 68, 56][index]} risk</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/[0.045] p-4">
            <p className="text-sm font-medium text-white">Roadmap timeline</p>
            <div className="mt-3 space-y-2">
              {roadmapSteps.map((step) => (
                <div key={step.title} className="rounded-xl border border-white/8 bg-[#0F172A]/70 px-3 py-2">
                  <p className="text-sm text-white">{step.title}</p>
                  <p className="mt-1 text-xs text-slate-400">{step.stage}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </GlassPanel>
  );
}

function TeacherMiniDashboard() {
  return (
    <GlassPanel className="h-full p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Teacher View</p>
          <h3 className="mt-2 text-xl font-semibold text-white">Class performance with intervention alerts</h3>
        </div>
        <Users2 className="h-5 w-5 text-sky-200" />
      </div>
      <div className="mt-6 grid gap-4">
        <div className="rounded-2xl border border-white/8 bg-[#0B1220]/70 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-white">Student comparison</p>
            <span className="text-xs text-slate-400">Risk vs mastery</span>
          </div>
          <div className="overflow-hidden">
            <BarChart width={460} height={160} data={teacherComparisonData} className="h-auto w-full">
              <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#64748B", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Bar dataKey="mastery" fill="#6366F1" radius={[8, 8, 0, 0]} />
              <Bar dataKey="risk" fill="#F59E0B" radius={[8, 8, 0, 0]} />
            </BarChart>
          </div>
        </div>
        <div className="grid gap-2">
          {[
            "3 learners need intervention before the next assessment.",
            "Maya Chen's confidence dropped 11% in optimization tasks.",
            "Class retention is strongest after shorter guided practice blocks.",
          ].map((item) => (
            <div key={item} className="flex items-start gap-3 rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-3">
              <CircleAlert className="mt-0.5 h-4 w-4 text-amber-300" />
              <p className="text-sm leading-6 text-slate-300">{item}</p>
            </div>
          ))}
        </div>
        <EmptyStateIllustration
          title="No unresolved alerts for cohort B"
          note="The system highlights quiet states too, so teachers can focus on the few students who actually need attention."
        />
      </div>
    </GlassPanel>
  );
}

function AdminMiniDashboard() {
  return (
    <GlassPanel className="h-full p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Admin View</p>
          <h3 className="mt-2 text-xl font-semibold text-white">Institution analytics across tenants and usage</h3>
        </div>
        <Building2 className="h-5 w-5 text-emerald-200" />
      </div>
      <div className="mt-6 grid gap-4">
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { label: "Active institutions", value: "28" },
            { label: "Weekly active learners", value: "4.8k" },
            { label: "Roadmaps generated", value: "12.4k" },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-3">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{item.label}</p>
              <p className="mt-2 text-2xl font-semibold text-white">{item.value}</p>
            </div>
          ))}
        </div>
        <div className="rounded-2xl border border-white/8 bg-[#0B1220]/70 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-white">Tenant overview</p>
            <span className="text-xs text-slate-400">Growth vs activation</span>
          </div>
          <div className="overflow-hidden">
            <AreaChart width={460} height={160} data={adminAnalyticsData} className="h-auto w-full">
              <defs>
                <linearGradient id="adminArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22C55E" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#22C55E" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: "#64748B", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Area type="monotone" dataKey="learners" stroke="#22C55E" fill="url(#adminArea)" strokeWidth={2.5} />
              <Line type="monotone" dataKey="active" stroke="#6366F1" strokeWidth={2.5} dot={false} />
            </AreaChart>
          </div>
        </div>
        <EmptyStateIllustration
          title="No tenant health regressions detected"
          note="A calm operational state is still part of the product story, so the UI makes system stability feel intentional."
        />
      </div>
    </GlassPanel>
  );
}

function MentorMiniDashboard() {
  return (
    <GlassPanel className="h-full p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">Mentor View</p>
          <h3 className="mt-2 text-xl font-semibold text-white">AI-supported mentoring with live context</h3>
        </div>
        <Bot className="h-5 w-5 text-indigo-200" />
      </div>
      <div className="mt-6 grid gap-4">
        <div className="rounded-2xl border border-white/8 bg-[#0B1220]/70 p-4">
          <div className="space-y-3">
            <div className="ml-auto max-w-[85%] rounded-2xl bg-[#6366F1] px-4 py-3 text-sm text-white">
              Maya is still hesitating on optimization updates. What should I focus on first?
            </div>
            <div className="max-w-[90%] rounded-2xl border border-white/8 bg-white/[0.05] px-4 py-3 text-sm leading-6 text-slate-200">
              Start with one worked example and ask for explanation after each step. Confidence is lagging behind actual performance, so guided retrieval should outperform more content.
            </div>
          </div>
        </div>
        <div className="grid gap-2">
          {[
            { label: "Intervention alert", value: "Confidence down 11%", tone: "text-amber-300" },
            { label: "Recommendation", value: "Run 28-min guided sprint", tone: "text-emerald-300" },
            { label: "Human handoff", value: "Brief ready for mentor", tone: "text-indigo-200" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-3">
              <p className="text-sm text-slate-300">{item.label}</p>
              <p className={cn("text-sm font-semibold", item.tone)}>{item.value}</p>
            </div>
          ))}
        </div>
        <EmptyStateIllustration
          title="No escalation needed yet"
          note="Mentor handoff remains on standby until the risk threshold crosses the intervention boundary."
        />
      </div>
    </GlassPanel>
  );
}

function RoleBasedSection() {
  return (
    <section className="mt-32">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionEyebrow>Role-based experience</SectionEyebrow>
          <h2 className="mt-6 max-w-3xl text-3xl font-semibold tracking-[-0.04em] text-white md:text-5xl">
            One platform, four operational views, zero generic dashboards.
          </h2>
        </div>
        <div className="max-w-xl space-y-3 text-sm leading-7 text-slate-300">
          {roleViews.map((view) => (
            <div key={view.key} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
              <span className="font-semibold text-white">{view.label}:</span> {view.description}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-12 grid gap-4 xl:grid-cols-2">
        <StudentMiniDashboard />
        <TeacherMiniDashboard />
        <AdminMiniDashboard />
        <MentorMiniDashboard />
      </div>
    </section>
  );
}

function IntelligenceStrip() {
  return (
    <section className="mt-32">
      <GlassPanel className="overflow-hidden p-6 md:p-8">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <SectionEyebrow>AI-native operations</SectionEyebrow>
            <h2 className="mt-6 max-w-2xl text-3xl font-semibold tracking-[-0.04em] text-white md:text-5xl">
              Intelligence is built into the workflow, not bolted onto the edges.
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-8 text-slate-300">
              The platform blends diagnostic evidence, topic graph reasoning, roadmap generation, mentor context, and institution analytics into one coherent operating system for learning.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {[
                { icon: Sparkles, title: "AI roadmap engine", note: "Sequences learning around mastery lift and retention pressure." },
                { icon: ShieldCheck, title: "Multi-tenant governance", note: "Institution-safe analytics with role-aware surfaces." },
                { icon: BrainCircuit, title: "Knowledge graph reasoning", note: "Maps prerequisite drag before it turns into learner friction." },
                { icon: CheckCircle2, title: "Operational progress loops", note: "Every session updates the next best action across roles." },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="rounded-2xl border border-white/8 bg-white/[0.045] px-4 py-4">
                    <Icon className="h-5 w-5 text-indigo-200" />
                    <p className="mt-3 text-sm font-semibold text-white">{item.title}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{item.note}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-4">
            <CommandPalettePreview />
            <AIRecommendationPanel />
            <div className="rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(11,18,32,0.88),rgba(11,18,32,0.74))] p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">System warmup</p>
                  <p className="mt-2 text-lg font-semibold text-white">Loading predictive context</p>
                </div>
                <Sparkles className="h-5 w-5 text-indigo-200" />
              </div>
              <div className="mt-4">
                <LoadingSkeleton />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <div className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-2 text-xs text-slate-300">
                  <Keyboard className="mr-2 inline h-3.5 w-3.5 text-slate-400" />
                  G P open learner profile
                </div>
                <div className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-2 text-xs text-slate-300">
                  <Keyboard className="mr-2 inline h-3.5 w-3.5 text-slate-400" />
                  G I intervention queue
                </div>
              </div>
            </div>
          </div>
        </div>
      </GlassPanel>
    </section>
  );
}

export default function LandingExperience() {
  return (
    <main
      className="relative min-h-screen overflow-hidden bg-[#0B1220] px-6 py-8 text-white"
      style={{ fontFamily: "Inter, Geist, ui-sans-serif, system-ui, sans-serif" }}
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="hero-orb left-[6%] top-16 h-72 w-72 bg-[rgba(99,102,241,0.24)]" />
        <div className="hero-orb right-[8%] top-24 h-80 w-80 bg-[rgba(34,211,238,0.12)] [animation-delay:2s]" />
        <div className="hero-orb bottom-[-6rem] left-[28%] h-96 w-[28rem] bg-[rgba(99,102,241,0.14)] [animation-delay:4s]" />
        <div className="landing-mesh absolute inset-0 opacity-70" />
      </div>

      <div className="relative mx-auto max-w-7xl">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-indigo-100">
              Learning Intelligence Platform
            </div>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300">
              AI-native mastery engine for students, teachers, mentors, admins, and institutions
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-[18px] border border-white/10 bg-white/[0.045] px-3 py-2 text-sm text-slate-300 backdrop-blur-xl md:flex">
              <Command className="h-4 w-4 text-slate-400" />
              <span>Command menu</span>
              <kbd className="rounded-md border border-white/10 bg-[#0F172A] px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-400">⌘K</kbd>
            </div>
            <div className="rounded-[20px] border border-white/10 bg-white/[0.045] p-1.5 backdrop-blur-xl">
              <ThemeToggle />
            </div>
          </div>
        </header>

        <section className="relative mt-16 grid gap-16 lg:grid-cols-[0.86fr_1.14fr] lg:items-start">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
            className="pt-4"
          >
            <SectionEyebrow>Intelligence that feels operational</SectionEyebrow>
            <h1 className="mt-8 max-w-3xl text-balance text-5xl font-semibold leading-[0.9] tracking-[-0.055em] text-white md:text-7xl">
              Turn every learner signal into adaptive AI that drives measurable mastery.
            </h1>
            <p className="mt-8 max-w-2xl text-lg leading-8 text-slate-300 md:text-[21px]">
              Diagnose weakness, map prerequisite drag, generate personalized roadmaps, surface mentor guidance, and monitor institutional learning performance inside one premium SaaS workspace.
            </p>

            <div className="mt-12 grid max-w-2xl gap-4 sm:grid-cols-3">
              {heroStats.map((item, index) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, delay: 0.12 + index * 0.08 }}
                >
                  <GlassPanel className="h-full px-4 py-4 hover:-translate-y-1 hover:border-[rgba(99,102,241,0.18)] hover:bg-[rgba(31,41,55,0.72)]">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">{item.label}</p>
                    <p className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-white">{item.value}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{item.detail}</p>
                  </GlassPanel>
                </motion.div>
              ))}
            </div>

            <div className="mt-12 flex flex-wrap gap-4">
              <RippleButton href="/auth">Start Learning</RippleButton>
              <RippleButton href={`/auth?next=${encodeURIComponent(appRoutes.student.dashboard)}`} variant="secondary">
                View Demo
              </RippleButton>
            </div>

            <div className="mt-12 flex flex-wrap gap-4 text-sm text-slate-300">
              {["Diagnostic engine", "Topic graph intelligence", "AI roadmap generator", "Role-aware analytics"].map((item) => (
                <div
                  key={item}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-2 transition duration-300 hover:border-white/16 hover:bg-white/8"
                >
                  {item}
                </div>
              ))}
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-6 text-sm text-slate-400">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-indigo-200" />
                <span>Live notifications across roles</span>
              </div>
              <div className="flex items-center gap-2">
                <Keyboard className="h-4 w-4 text-indigo-200" />
                <span>Keyboard-first workflows built in</span>
              </div>
            </div>
          </motion.div>

          <HeroDashboard />
        </section>

        <ProductFlowSection />
        <RoleBasedSection />
        <IntelligenceStrip />
      </div>
    </main>
  );
}
