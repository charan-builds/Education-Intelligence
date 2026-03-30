import { Shield } from "lucide-react";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { featureCards } from "@/components/landing-new/content";

export default function LandingFeatures() {
  return (
    <section id="features" className="relative py-28">
      <div className="absolute inset-0">
        <div className="absolute right-[8%] top-0 h-[360px] w-[360px] rounded-full bg-yellow-200/30 blur-[120px]" />
      </div>
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="Platform Features"
          title="Built for"
          accent="excellence"
          description="The imported premium marketing design is now aligned with the real SaaS product architecture."
          icon={Shield}
        />

        <div className="mt-16 grid gap-8 md:grid-cols-2 xl:grid-cols-3">
          {featureCards.map((feature) => (
            <article
              key={feature.title}
              className="group relative h-full rounded-[2rem] border-2 border-slate-200 bg-white/80 p-8 shadow-xl backdrop-blur-xl transition duration-300 hover:-translate-y-2 hover:shadow-2xl"
            >
              <div className={`absolute inset-0 rounded-[2rem] bg-gradient-to-br ${feature.gradientClassName} opacity-0 transition duration-300 group-hover:opacity-5`} />
              <div className={`relative inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${feature.gradientClassName} shadow-lg`}>
                <feature.icon className="h-8 w-8 text-white" />
              </div>
              <h3 className="relative mt-6 text-2xl font-bold text-slate-900">{feature.title}</h3>
              <p className="relative mt-3 text-base leading-7 text-slate-600">{feature.description}</p>
              <div className={`relative mt-6 inline-flex rounded-xl bg-gradient-to-br ${feature.tintClassName} px-4 py-2 text-sm font-semibold text-slate-800`}>
                {feature.stat}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
