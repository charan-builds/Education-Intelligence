"use client";

import { useRouter } from "next/navigation";

import LandingCta from "@/components/landing/LandingCta";
import LandingFeatureGrid from "@/components/landing/LandingFeatureGrid";
import LandingHero from "@/components/landing/LandingHero";
import LandingJourney from "@/components/landing/LandingJourney";

export default function LandingPage() {
  const router = useRouter();

  function handleStart() {
    router.push("/auth");
  }

  return (
    <main className="space-y-8 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
      <LandingHero onStart={handleStart} />
      <LandingFeatureGrid />
      <LandingJourney />
      <LandingCta onStart={handleStart} />
    </main>
  );
}
