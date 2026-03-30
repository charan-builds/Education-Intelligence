import { ArrowDown, Rocket } from "lucide-react";
import Link from "next/link";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { journeySteps } from "@/components/landing-new/content";

type LandingJourneyProps = {
  dashboardHref: string;
  isAuthenticated: boolean;
};

export default function LandingJourney({ dashboardHref, isAuthenticated }: LandingJourneyProps) {
  return (
    <section id="journey" className="relative py-28">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="The Journey"
          title="From data to"
          accent="mastery"
          description="A clear four-step story from diagnostics to live progress, re-created in native Next.js components."
          icon={Rocket}
        />

        <div className="relative mt-20 space-y-10 lg:space-y-16">
          <div className="absolute left-8 top-10 hidden h-[calc(100%-5rem)] w-px bg-gradient-to-b from-yellow-400 via-amber-500 to-yellow-300 lg:block" />
          {journeySteps.map((step, index) => (
            <div key={step.step} className="relative grid gap-6 lg:grid-cols-[90px_1fr_0.95fr] lg:gap-10">
              <div className="hidden lg:flex lg:justify-center">
                <div className={`flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br ${step.gradientClassName} text-lg font-bold text-white shadow-xl`}>
                  {step.step}
                </div>
              </div>
              <div className="rounded-[2rem] border border-slate-200 bg-white/80 p-8 shadow-lg backdrop-blur-xl">
                <div className="inline-flex items-center gap-3 rounded-full border border-slate-200 bg-slate-50 px-4 py-2">
                  <span className="text-xs font-bold tracking-[0.24em] text-slate-400">STEP</span>
                  <span className={`text-lg font-bold bg-gradient-to-r ${step.gradientClassName} bg-clip-text text-transparent`}>{step.step}</span>
                </div>
                <h3 className="mt-6 text-3xl font-bold text-slate-900">{step.title}</h3>
                <p className="mt-4 text-base leading-7 text-slate-700">{step.description}</p>
                <p className="mt-4 text-sm font-medium text-slate-500">{step.detail}</p>
              </div>
              <div className={`rounded-[2rem] border-2 border-slate-200 bg-gradient-to-br ${step.tintClassName} p-8 shadow-xl`}>
                <div className={`flex h-20 w-20 items-center justify-center rounded-[1.5rem] bg-gradient-to-br ${step.gradientClassName} shadow-xl`}>
                  <step.icon className="h-10 w-10 text-white" />
                </div>
                <div className="mt-8 space-y-3">
                  {[0, 1, 2].map((barIndex) => (
                    <div key={barIndex} className="rounded-2xl border border-slate-200 bg-white/75 p-4">
                      <div className="flex items-center gap-3">
                        <div className={`h-2 w-2 rounded-full bg-gradient-to-r ${step.gradientClassName}`} />
                        <div className="h-2 flex-1 rounded-full bg-slate-200">
                          <div
                            className={`h-2 rounded-full bg-gradient-to-r ${step.gradientClassName}`}
                            style={{ width: `${70 + barIndex * 10}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {index < journeySteps.length - 1 ? (
                  <div className="mt-6 flex justify-center lg:hidden">
                    <ArrowDown className="h-6 w-6 text-yellow-600" />
                  </div>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <Link
            href={isAuthenticated ? dashboardHref : "/register"}
            className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-yellow-400 to-amber-500 px-8 py-4 text-base font-bold text-white shadow-2xl shadow-yellow-500/25 transition hover:-translate-y-0.5 hover:from-yellow-500 hover:to-amber-600"
          >
            {isAuthenticated ? "Go to Dashboard" : "Get Started"}
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">No credit card required. Existing product routes stay untouched.</p>
        </div>
      </div>
    </section>
  );
}
