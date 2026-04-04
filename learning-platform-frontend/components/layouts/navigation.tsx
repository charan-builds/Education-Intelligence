"use client";

import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Bell,
  BookOpen,
  Briefcase,
  BrainCircuit,
  Building2,
  ChartArea,
  ChartPie,
  Cpu,
  Flag,
  GraduationCap,
  LayoutDashboard,
  Layers3,
  LifeBuoy,
  MessagesSquare,
  Network,
  Radar,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { appRoutes } from "@/utils/appRoutes";

export type AppNavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  match?: string[];
};

export const studentNav: AppNavItem[] = [
  { label: "Dashboard", href: appRoutes.student.dashboard, icon: LayoutDashboard },
  { label: "Goals", href: appRoutes.student.goals, icon: GraduationCap },
  { label: "Diagnostic", href: appRoutes.student.diagnostic, icon: Radar, match: [appRoutes.student.diagnostic, appRoutes.student.diagnosticResult] },
  { label: "Roadmap", href: appRoutes.student.roadmap, icon: Network },
  { label: "Mentor", href: appRoutes.student.mentor, icon: Sparkles },
  { label: "Progress", href: appRoutes.student.progress, icon: ChartArea },
  { label: "Profile", href: appRoutes.student.profile, icon: ShieldCheck },
  { label: "Network", href: appRoutes.student.network, icon: Users },
  { label: "Digital Twin", href: appRoutes.student.digitalTwin, icon: Cpu },
  { label: "Career", href: appRoutes.student.career, icon: Briefcase },
  { label: "Notifications", href: appRoutes.student.notifications, icon: Bell },
];

export const independentLearnerNav: AppNavItem[] = [
  { label: "Dashboard", href: appRoutes.independentLearner.dashboard, icon: LayoutDashboard },
  { label: "Goals", href: appRoutes.independentLearner.goals, icon: GraduationCap },
  {
    label: "Diagnostic",
    href: appRoutes.independentLearner.diagnostic,
    icon: Radar,
    match: [appRoutes.independentLearner.diagnostic, appRoutes.independentLearner.diagnosticResult],
  },
  { label: "Roadmap", href: appRoutes.independentLearner.roadmap, icon: Network },
  { label: "Progress", href: appRoutes.independentLearner.progress, icon: ChartArea },
  { label: "Profile", href: appRoutes.independentLearner.profile, icon: ShieldCheck },
  { label: "Mentor", href: appRoutes.independentLearner.mentor, icon: Sparkles },
];

export const teacherNav: AppNavItem[] = [
  { label: "Dashboard", href: appRoutes.teacher.dashboard, icon: LayoutDashboard },
  { label: "Students", href: appRoutes.teacher.students, icon: Users },
  { label: "Insights", href: appRoutes.teacher.insights, icon: ChartPie },
];

export const adminNav: AppNavItem[] = [
  { label: "Dashboard", href: appRoutes.admin.dashboard, icon: LayoutDashboard },
  { label: "Users", href: appRoutes.admin.users, icon: Users },
  { label: "Content", href: appRoutes.admin.content, icon: BookOpen },
  { label: "Goals", href: appRoutes.admin.goals, icon: GraduationCap },
  { label: "Community", href: appRoutes.admin.community, icon: MessagesSquare },
  { label: "Ecosystem", href: appRoutes.admin.ecosystem, icon: Layers3 },
  { label: "ML Platform", href: appRoutes.admin.ml, icon: BrainCircuit },
  { label: "Feature Flags", href: appRoutes.admin.featureFlags, icon: Flag },
];

export const superAdminNav: AppNavItem[] = [
  { label: "Dashboard", href: appRoutes.superAdmin.dashboard, icon: LayoutDashboard },
  { label: "Tenants", href: appRoutes.superAdmin.tenants, icon: Building2 },
  { label: "Outbox", href: appRoutes.superAdmin.outbox, icon: Activity },
  { label: "Health", href: appRoutes.superAdmin.health, icon: ShieldCheck },
];

export const mentorNav: AppNavItem[] = [
  { label: "Dashboard", href: appRoutes.mentor.dashboard, icon: LayoutDashboard },
  { label: "Network", href: appRoutes.mentor.network, icon: Users },
  { label: "Chat", href: appRoutes.mentor.chat, icon: MessagesSquare },
  { label: "Recommendations", href: appRoutes.mentor.dashboard, icon: Sparkles, match: [appRoutes.mentor.dashboard] },
  { label: "Support Hub", href: appRoutes.mentor.network, icon: LifeBuoy, match: [appRoutes.mentor.network] },
];

export function matchNavItem(pathname: string, item: AppNavItem): boolean {
  const candidates = item.match ?? [item.href];
  return candidates.some((candidate) => pathname === candidate || pathname.startsWith(`${candidate}/`));
}
