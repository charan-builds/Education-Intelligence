"use client";

import { motion } from "framer-motion";
import { ArrowRight, BrainCircuit, LineChart, Sparkles } from "lucide-react";

import Logo from "@/components/brand/Logo";
import Button from "@/components/ui/Button";

type LandingHeroProps = {
  onStart: () => void;
};

const highlights = [
  "Adaptive diagnostics connected to FastAPI",
  "Roadmaps generated from real learning signals",
  "Production-ready auth, Redis, Celery, and PostgreSQL stack",
];

export default function LandingHero({ onStart }: LandingHeroProps) {
  return (
    <section className="relative overflow-hidden rounded-[40px] border border-slate-200/70 bg-slate-950 px-6 py-8 text-white shadow-2xl sm:px-10 sm:py-12">
      <div className="landing-grid landing-mesh absolute inset-0 opacity-90" />
      <div className="hero-orb left-[-8%] top-[-10%] h-52 w-52 bg-teal-400/25" />
      <div className="hero-orb right-[-4%] top-[12%] h-60 w-60 bg-orange-400/20" />
      <div className="hero-orb bottom-[-18%] left-[22%] h-64 w-64 bg-sky-400/15" />

      <div className="relative z-10 mx-auto grid max-w-6xl gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div>
          <Logo />
          <p className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-teal-100">
            <Sparkles className="h-3.5 w-3.5" />
            Learning Intelligence Platform
          </p>
          <h1 className="mt-6 max-w-3xl text-balance text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
            Ship personalized learning journeys with a frontend that finally matches the backend.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            Learnova AI turns diagnostics, roadmap generation, and learner progress into one guided SaaS experience.
            Start on the landing page, authenticate, complete a diagnostic, and step into a roadmap that stays connected to your live backend.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Button onClick={onStart} className="min-w-[180px] bg-white text-slate-950 hover:bg-slate-100">
              Start Learning
              <ArrowRight className="h-4 w-4" />
            </Button>
            <a
              href="#platform-flow"
              className="inline-flex items-center justify-center rounded-2xl border border-white/15 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Explore the flow
            </a>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {highlights.map((item) => (
              <div key={item} className="rounded-[24px] border border-white/10 bg-white/5 px-4 py-4 text-sm text-slate-200 backdrop-blur">
                {item}
              </div>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="rounded-[34px] border border-white/10 bg-white/6 p-6 backdrop-blur-xl"
        >
          <div className="grid gap-4">
            <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-400/15 text-teal-200">
                  <BrainCircuit className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Diagnostic Engine</p>
                  <p className="text-sm text-slate-300">Start a test, score weak topics, and trigger roadmap generation.</p>
                </div>
              </div>
            </div>

            <div className="rounded-[28px] border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-300">Platform flow</p>
              <div id="platform-flow" className="mt-4 space-y-3">
                {[
                  "Landing",
                  "Auth",
                  "Dashboard",
                  "Diagnostic",
                  "Roadmap",
                ].map((step, index) => (
                  <div key={step} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-xs font-bold text-slate-950">
                      {index + 1}
                    </div>
                    <p className="font-medium text-white">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-400/15 text-orange-200">
                  <LineChart className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Roadmap Visibility</p>
                  <p className="text-sm text-slate-300">Track progress, deadlines, and next steps from the same experience.</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
