/* eslint-disable @next/next/no-css-tags */
import type { Metadata } from "next";

import PremiumLandingMount from "@/components/landing/PremiumLandingMount";

export const metadata: Metadata = {
  title: "Learnova AI — Turn Learning Into Intelligence",
  description: "AI-powered diagnostics that detect learning gaps, generate personalized roadmaps, and accelerate mastery.",
};

export default function Home() {
  return (
    <>
      <style>{`
        html {
          background: #fffdf6 !important;
          color-scheme: light !important;
        }

        body {
          background:
            radial-gradient(circle at 12% 18%, rgba(250, 204, 21, 0.18), transparent 22%),
            radial-gradient(circle at 84% 16%, rgba(251, 191, 36, 0.1), transparent 18%),
            radial-gradient(circle at 34% 86%, rgba(252, 211, 77, 0.1), transparent 24%),
            linear-gradient(180deg, #fffdf6 0%, #fffef9 100%) !important;
          color: #111827 !important;
        }
      `}</style>
      <link
        rel="stylesheet"
        href="/premium/assets/index-DNRaT4GT.css"
        crossOrigin="anonymous"
      />
      <PremiumLandingMount />
    </>
  );
}
