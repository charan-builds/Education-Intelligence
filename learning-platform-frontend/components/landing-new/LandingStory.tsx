import { Sparkles } from "lucide-react";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { storyCards } from "@/components/landing-new/content";

export default function LandingStory() {
  return (
    <section className="relative py-28">
      <div className="absolute inset-0">
        <div className="absolute left-[10%] top-[8%] h-[320px] w-[320px] rounded-full bg-yellow-300/20 blur-[120px]" />
      </div>
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="How It Works"
          title="Intelligence that"
          accent="evolves"
          description="The new landing experience tells the product story clearly while still pointing into the existing SaaS application."
          icon={Sparkles}
        />

        <div className="mt-16 grid gap-8 lg:grid-cols-2">
          {storyCards.map((card) => (
            <article
              key={card.title}
              className={`rounded-[2rem] border-2 border-slate-200 bg-gradient-to-br ${card.tintClassName} p-8 shadow-xl`}
            >
              <div className={`inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${card.gradientClassName} shadow-lg`}>
                <card.icon className="h-7 w-7 text-white" />
              </div>
              <h3 className="mt-6 text-2xl font-bold text-slate-900">{card.title}</h3>
              <p className="mt-3 text-base leading-7 text-slate-700">{card.description}</p>
              <div className="mt-5 inline-flex rounded-xl border border-slate-200 bg-white/85 px-4 py-2 text-sm font-semibold text-slate-700">
                {card.stat}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
