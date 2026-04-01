import type { Metadata } from "next";

import LandingPage from "@/components/landing-new/LandingPage";

export const metadata: Metadata = {
  title: "Learnova AI — Turn Learning Into Intelligence",
  description: "AI-powered diagnostics, personalized roadmaps, and role-based learning operations in one connected SaaS platform.",
};

export default function Home() {
  return <LandingPage />;
}
