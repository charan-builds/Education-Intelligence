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

export default function LandingPage() {
  const dashboardHref = "/dashboard";
  const isAuthenticated = false;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(196,181,253,0.34),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(216,180,254,0.22),_transparent_30%),linear-gradient(180deg,_#f8f5ff_0%,_#ffffff_100%)] text-slate-950">
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
