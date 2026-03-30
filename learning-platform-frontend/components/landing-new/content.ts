import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  BookOpen,
  Brain,
  Clock3,
  GraduationCap,
  LineChart,
  MessageSquareMore,
  Rocket,
  Shield,
  Sparkles,
  Star,
  Target,
  Trophy,
  Users,
  Zap,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
};

export type Stat = {
  label: string;
  value: string;
  accentClassName: string;
};

export type Feature = {
  icon: LucideIcon;
  title: string;
  description: string;
  stat: string;
  gradientClassName: string;
  tintClassName: string;
};

export type StoryCard = {
  icon: LucideIcon;
  title: string;
  description: string;
  stat: string;
  gradientClassName: string;
  tintClassName: string;
};

export type JourneyStep = {
  step: string;
  title: string;
  description: string;
  detail: string;
  icon: LucideIcon;
  gradientClassName: string;
  tintClassName: string;
};

export type Metric = {
  icon: LucideIcon;
  label: string;
  value: string;
  gradientClassName: string;
  tintClassName: string;
};

export type Testimonial = {
  name: string;
  role: string;
  quote: string;
  result: string;
  avatar: string;
  gradientClassName: string;
};

export type PricingTier = {
  name: string;
  price: string;
  description: string;
  ctaLabel: string;
  featured?: boolean;
  features: string[];
};

export type FaqItem = {
  question: string;
  answer: string;
};

export const navItems: NavItem[] = [
  { label: "Features", href: "#features" },
  { label: "Journey", href: "#journey" },
  { label: "Pricing", href: "#pricing" },
  { label: "Testimonials", href: "#testimonials" },
];

export const heroStats: Stat[] = [
  { label: "Success Rate", value: "98%", accentClassName: "text-emerald-600" },
  { label: "Active Learners", value: "2.5M+", accentClassName: "text-sky-600" },
  { label: "AI Accuracy", value: "99.2%", accentClassName: "text-amber-600" },
];

export const featureCards: Feature[] = [
  {
    icon: Brain,
    title: "Neural Learning Analysis",
    description: "AI models surface learning gaps and adapt content around each learner's pace and pattern.",
    stat: "99.2% accuracy",
    gradientClassName: "from-sky-500 to-indigo-600",
    tintClassName: "from-sky-100 to-indigo-100",
  },
  {
    icon: Target,
    title: "Precision Roadmaps",
    description: "Personalized study paths convert diagnostics into clear next steps for faster mastery.",
    stat: "3x faster progress",
    gradientClassName: "from-emerald-500 to-teal-600",
    tintClassName: "from-emerald-100 to-teal-100",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "The experience feels polished on the surface while preserving the secure SaaS foundation underneath.",
    stat: "Production ready",
    gradientClassName: "from-slate-500 to-slate-700",
    tintClassName: "from-slate-100 to-slate-200",
  },
  {
    icon: LineChart,
    title: "Predictive Analytics",
    description: "Track performance trends early and identify interventions before students fall behind.",
    stat: "94% prediction rate",
    gradientClassName: "from-fuchsia-500 to-rose-600",
    tintClassName: "from-fuchsia-100 to-rose-100",
  },
  {
    icon: Users,
    title: "Collaborative Intelligence",
    description: "Teachers, mentors, and students can align around the same real-time signals and recommendations.",
    stat: "Multi-role visibility",
    gradientClassName: "from-orange-500 to-amber-600",
    tintClassName: "from-orange-100 to-amber-100",
  },
  {
    icon: Zap,
    title: "Live Adaptation",
    description: "Every activity can feed the next recommendation so the roadmap stays relevant as progress changes.",
    stat: "Updates every minute",
    gradientClassName: "from-yellow-500 to-amber-500",
    tintClassName: "from-yellow-100 to-amber-100",
  },
];

export const storyCards: StoryCard[] = [
  {
    icon: Brain,
    title: "AI Detects Learning Gaps",
    description: "Pattern-aware analysis spots weak areas before they turn into stalled momentum.",
    stat: "Real-time diagnostics",
    gradientClassName: "from-sky-500 to-indigo-600",
    tintClassName: "from-sky-100 to-indigo-100",
  },
  {
    icon: Target,
    title: "Roadmaps Stay Personalized",
    description: "Each learner gets a path tuned to strengths, pace, and current mastery.",
    stat: "Adaptive planning",
    gradientClassName: "from-emerald-500 to-teal-600",
    tintClassName: "from-emerald-100 to-teal-100",
  },
  {
    icon: Sparkles,
    title: "Recommendations Keep Evolving",
    description: "Progress signals continuously refine what to study next and where to intervene.",
    stat: "Continuous optimization",
    gradientClassName: "from-yellow-500 to-amber-600",
    tintClassName: "from-yellow-100 to-amber-100",
  },
  {
    icon: BarChart3,
    title: "Teams See the Same Truth",
    description: "Dashboards align students, teachers, and admins around one high-signal picture of progress.",
    stat: "Shared insight layer",
    gradientClassName: "from-fuchsia-500 to-rose-600",
    tintClassName: "from-fuchsia-100 to-rose-100",
  },
];

export const journeySteps: JourneyStep[] = [
  {
    step: "01",
    title: "Run diagnostics",
    description: "Start with structured assessments, performance inputs, and learning behavior signals.",
    detail: "Upload or connect your existing learning data in minutes.",
    icon: Rocket,
    gradientClassName: "from-sky-500 to-indigo-600",
    tintClassName: "from-sky-100 to-indigo-100",
  },
  {
    step: "02",
    title: "Surface patterns",
    description: "The platform isolates what is blocking progress and what is accelerating it.",
    detail: "Weak areas, confidence signals, and trend changes become visible immediately.",
    icon: Brain,
    gradientClassName: "from-fuchsia-500 to-rose-600",
    tintClassName: "from-fuchsia-100 to-rose-100",
  },
  {
    step: "03",
    title: "Generate roadmaps",
    description: "Recommendations turn into a clear sequence of goals, topics, and interventions.",
    detail: "Every next step is tied back to measurable progress.",
    icon: Target,
    gradientClassName: "from-emerald-500 to-teal-600",
    tintClassName: "from-emerald-100 to-teal-100",
  },
  {
    step: "04",
    title: "Track mastery",
    description: "Live dashboards show improvement, completion, risk, and momentum across the product.",
    detail: "Students and teams can respond quickly instead of waiting for a later report.",
    icon: Trophy,
    gradientClassName: "from-yellow-500 to-amber-600",
    tintClassName: "from-yellow-100 to-amber-100",
  },
];

export const metricCards: Metric[] = [
  {
    icon: Users,
    label: "Active Learners",
    value: "2.5M+",
    gradientClassName: "from-sky-500 to-indigo-600",
    tintClassName: "from-sky-100 to-indigo-100",
  },
  {
    icon: BookOpen,
    label: "Lessons Completed",
    value: "15M+",
    gradientClassName: "from-emerald-500 to-teal-600",
    tintClassName: "from-emerald-100 to-teal-100",
  },
  {
    icon: Star,
    label: "Success Rate",
    value: "98.5%",
    gradientClassName: "from-yellow-500 to-amber-600",
    tintClassName: "from-yellow-100 to-amber-100",
  },
  {
    icon: Clock3,
    label: "Time Saved Weekly",
    value: "45h",
    gradientClassName: "from-fuchsia-500 to-rose-600",
    tintClassName: "from-fuchsia-100 to-rose-100",
  },
];

export const testimonials: Testimonial[] = [
  {
    name: "Sarah Mitchell",
    role: "University Student",
    quote: "The roadmap felt like it actually understood how I learn. I stopped guessing and started improving every week.",
    result: "+47% improvement",
    avatar: "SM",
    gradientClassName: "from-sky-500 to-indigo-600",
  },
  {
    name: "Dr. James Chen",
    role: "Teacher",
    quote: "The dashboards help me see who needs support before a student disappears into the noise of a big cohort.",
    result: "150 students managed",
    avatar: "JC",
    gradientClassName: "from-emerald-500 to-teal-600",
  },
  {
    name: "Emily Rodriguez",
    role: "Education Director",
    quote: "We got a premium experience on the homepage without sacrificing the workflows our teams already rely on.",
    result: "+63% engagement",
    avatar: "ER",
    gradientClassName: "from-yellow-500 to-amber-600",
  },
];

export const pricingTiers: PricingTier[] = [
  {
    name: "Starter",
    price: "Free",
    description: "Great for individuals exploring AI-assisted learning.",
    ctaLabel: "Create Account",
    features: ["14-day guided onboarding", "Diagnostics and roadmap access", "Core dashboard experience"],
  },
  {
    name: "Growth",
    price: "$29/mo",
    description: "Best for serious learners and small teams that want more signal.",
    ctaLabel: "Start Free Trial",
    featured: true,
    features: ["Everything in Starter", "Advanced analytics and recommendations", "Priority roadmap updates"],
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For institutions that need scale, governance, and multi-role coordination.",
    ctaLabel: "Contact Sales",
    features: ["Role-based coordination", "Expanded operational visibility", "Launch planning and support"],
  },
];

export const faqItems: FaqItem[] = [
  {
    question: "Will this replace my existing auth and dashboards?",
    answer: "No. The new landing page only replaces the homepage presentation layer. Existing auth flows, routing, and dashboard behavior stay in place.",
  },
  {
    question: "Where do users go when they click a CTA?",
    answer: "Primary calls to action route to register or login, while authenticated users also see a dashboard shortcut.",
  },
  {
    question: "Is the new landing page reusable?",
    answer: "Yes. Each section is isolated under components/landing-new so the homepage stays clean and future edits remain localized.",
  },
];

export const footerLinks = {
  product: ["Features", "Pricing", "Dashboards", "Security"],
  resources: ["Documentation", "Guides", "Community", "Support"],
  company: ["About", "Careers", "Contact", "Privacy"],
};

export const dashboardPreviewCourses = [
  { title: "Advanced Calculus", activeUsers: 1247, gradientClassName: "from-sky-500 to-indigo-600" },
  { title: "Physics 101", activeUsers: 892, gradientClassName: "from-emerald-500 to-teal-600" },
  { title: "Creative Writing", activeUsers: 634, gradientClassName: "from-yellow-500 to-amber-600" },
];

export const dashboardStats = [
  { label: "Avg Score", value: "80.5%", accentClassName: "text-sky-600" },
  { label: "Growth Rate", value: "5.7%", accentClassName: "text-emerald-600" },
  { label: "Top Rank", value: "Top 5%", accentClassName: "text-fuchsia-600" },
];

export const dashboardSkills = [
  { name: "Math", value: 85, color: "#3B82F6" },
  { name: "Science", value: 92, color: "#10B981" },
  { name: "English", value: 78, color: "#F59E0B" },
  { name: "History", value: 88, color: "#8B5CF6" },
];

export const dashboardActivity = [
  { day: "Mon", hours: 3.5 },
  { day: "Tue", hours: 4.2 },
  { day: "Wed", hours: 3.8 },
  { day: "Thu", hours: 5.1 },
  { day: "Fri", hours: 4.5 },
  { day: "Sat", hours: 2.3 },
  { day: "Sun", hours: 1.8 },
];

export const dashboardPerformance = [
  { month: "Jan", score: 65 },
  { month: "Feb", score: 72 },
  { month: "Mar", score: 78 },
  { month: "Apr", score: 85 },
  { month: "May", score: 89 },
  { month: "Jun", score: 94 },
];

export const liveFeed = [
  { user: "Sarah M.", action: "completed Advanced Calculus", time: "2s ago", gradientClassName: "from-sky-500 to-indigo-600" },
  { user: "John K.", action: "achieved 95% in Physics Quiz", time: "5s ago", gradientClassName: "from-emerald-500 to-teal-600" },
  { user: "Emma R.", action: "started a new AI roadmap", time: "8s ago", gradientClassName: "from-fuchsia-500 to-rose-600" },
];

export const trustBadges = ["Harvard", "Stanford", "MIT", "Oxford", "Cambridge"];

export const footerIcons = [
  { icon: MessageSquareMore, label: "Community" },
  { icon: GraduationCap, label: "Education" },
  { icon: Shield, label: "Security" },
];
