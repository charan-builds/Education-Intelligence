"use client";

import { useAuth } from "@/hooks/useAuth";
import LandingDashboardPreview from "@/components/landing-new/LandingDashboardPreview";
import LandingFaq from "@/components/landing-new/LandingFaq";
import LandingFeatures from "@/components/landing-new/LandingFeatures";
import LandingFinalCta from "@/components/landing-new/LandingFinalCta";
import LandingFooter from "@/components/landing-new/LandingFooter";
import LandingHero from "@/components/landing-new/LandingHero";
import LandingJourney from "@/components/landing-new/LandingJourney";
import LandingMetrics from "@/components/landing-new/LandingMetrics";
import LandingNavigation from "@/components/landing-new/LandingNavigation";
import LandingPricing from "@/components/landing-new/LandingPricing";
import LandingStory from "@/components/landing-new/LandingStory";
import LandingTestimonials from "@/components/landing-new/LandingTestimonials";
import { getRoleRedirectPath } from "@/utils/roleRedirect";

export default function LandingPage() {
  const { isAuthenticated, role } = useAuth();
  const dashboardHref = getRoleRedirectPath(role);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-white to-amber-50 text-slate-950">
      <LandingNavigation dashboardHref={dashboardHref} isAuthenticated={isAuthenticated} />
      <main>
        <LandingHero dashboardHref={dashboardHref} isAuthenticated={isAuthenticated} />
        <LandingStory />
        <LandingJourney dashboardHref={dashboardHref} isAuthenticated={isAuthenticated} />
        <LandingFeatures />
        <LandingDashboardPreview />
        <LandingMetrics />
        <LandingTestimonials />
        <LandingPricing dashboardHref={dashboardHref} isAuthenticated={isAuthenticated} />
        <LandingFaq />
        <LandingFinalCta dashboardHref={dashboardHref} isAuthenticated={isAuthenticated} />
      </main>
      <LandingFooter dashboardHref={dashboardHref} />
    </div>
  );
}
