import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Learnova AI Workspace",
  description: "Role-based learning intelligence workspace with diagnostics, roadmaps, and analytics.",
};

export default function Home() {
  redirect("/auth");
}
