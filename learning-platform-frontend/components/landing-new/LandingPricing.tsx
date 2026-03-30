import { BadgeCheck } from "lucide-react";
import Link from "next/link";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { pricingTiers } from "@/components/landing-new/content";

type LandingPricingProps = {
  dashboardHref: string;
  isAuthenticated: boolean;
};

export default function LandingPricing({ dashboardHref, isAuthenticated }: LandingPricingProps) {
  return (
    <section id="pricing" className="relative py-28">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="Pricing"
          title="Choose the"
          accent="right fit"
          description="Pricing is presented as a product story on the homepage, while signup still flows into the existing authentication experience."
          icon={BadgeCheck}
        />

        <div className="mt-16 grid gap-8 lg:grid-cols-3">
          {pricingTiers.map((tier) => (
            <article
              key={tier.name}
              className={`rounded-[2rem] border-2 p-8 shadow-2xl ${
                tier.featured
                  ? "border-yellow-300 bg-gradient-to-br from-yellow-100 to-amber-100"
                  : "border-slate-200 bg-white/80 backdrop-blur-xl"
              }`}
            >
              {tier.featured ? (
                <div className="inline-flex rounded-full bg-slate-950 px-3 py-1 text-xs font-bold uppercase tracking-[0.24em] text-white">Most Popular</div>
              ) : null}
              <h3 className="mt-4 text-2xl font-bold text-slate-900">{tier.name}</h3>
              <div className="mt-3 text-5xl font-bold text-slate-950">{tier.price}</div>
              <p className="mt-4 text-base leading-7 text-slate-600">{tier.description}</p>

              <div className="mt-8">
                <Link
                  href={isAuthenticated ? dashboardHref : tier.name === "Enterprise" ? "/login" : "/register"}
                  className={`inline-flex w-full items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold transition ${
                    tier.featured ? "bg-slate-950 text-white hover:bg-slate-900" : "border border-slate-200 bg-white text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  {isAuthenticated ? "Go to Dashboard" : tier.ctaLabel}
                </Link>
              </div>

              <ul className="mt-8 space-y-4">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm leading-7 text-slate-700">
                    <BadgeCheck className="mt-1 h-4 w-4 flex-none text-emerald-600" />
                    {feature}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
