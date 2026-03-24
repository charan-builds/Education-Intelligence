"use client";

import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Bell,
  BookOpen,
  Briefcase,
  Bot,
  BrainCircuit,
  Building2,
  ChartArea,
  ChartPie,
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

export type AppNavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  match?: string[];
};

export const studentNav: AppNavItem[] = [
  { label: "Dashboard", href: "/student/dashboard", icon: LayoutDashboard },
  { label: "Diagnostic", href: "/student/diagnostic", icon: Radar },
  { label: "Roadmap", href: "/student/roadmap", icon: Network },
  { label: "Progress", href: "/student/progress", icon: ChartArea },
  { label: "Career", href: "/student/career", icon: Briefcase },
  { label: "Notifications", href: "/student/notifications", icon: Bell },
  { label: "Mentor", href: "/mentor/dashboard", icon: Bot, match: ["/mentor"] },
];

export const teacherNav: AppNavItem[] = [
  { label: "Dashboard", href: "/teacher/dashboard", icon: LayoutDashboard },
  { label: "Students", href: "/teacher/students", icon: Users },
  { label: "Insights", href: "/teacher/insights", icon: ChartPie },
  { label: "Mentor View", href: "/mentor/dashboard", icon: BrainCircuit, match: ["/mentor"] },
];

export const adminNav: AppNavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { label: "Users", href: "/admin/users", icon: Users },
  { label: "Content", href: "/admin/content", icon: BookOpen },
  { label: "Goals", href: "/admin/goals", icon: GraduationCap },
  { label: "Community", href: "/admin/community", icon: MessagesSquare },
  { label: "Ecosystem", href: "/admin/ecosystem", icon: Layers3 },
  { label: "ML Platform", href: "/admin/ml", icon: BrainCircuit },
  { label: "Feature Flags", href: "/admin/feature-flags", icon: Flag },
];

export const superAdminNav: AppNavItem[] = [
  { label: "Dashboard", href: "/super-admin/dashboard", icon: LayoutDashboard },
  { label: "Tenants", href: "/super-admin/tenants", icon: Building2 },
  { label: "Outbox", href: "/super-admin/outbox", icon: Activity },
  { label: "Health", href: "/super-admin/health", icon: ShieldCheck },
  { label: "Feature Flags", href: "/admin/feature-flags", icon: Flag, match: ["/admin/feature-flags"] },
];

export const mentorNav: AppNavItem[] = [
  { label: "Dashboard", href: "/mentor/dashboard", icon: LayoutDashboard },
  { label: "Chat", href: "/mentor/chat", icon: MessagesSquare },
  { label: "Guidance", href: "/student/notifications", icon: Sparkles, match: ["/student/notifications"] },
  { label: "Support", href: "/teacher/insights", icon: LifeBuoy, match: ["/teacher/insights"] },
];

export function matchNavItem(pathname: string, item: AppNavItem): boolean {
  const candidates = item.match ?? [item.href];
  return candidates.some((candidate) => pathname === candidate || pathname.startsWith(`${candidate}/`));
}
