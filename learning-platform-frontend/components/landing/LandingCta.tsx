"use client";

import { ArrowRight } from "lucide-react";

import Button from "@/components/ui/Button";

type LandingCtaProps = {
  onStart: () => void;
};

export default function LandingCta({ onStart }: LandingCtaProps) {
  return (
    <section className="mx-auto max-w-6xl rounded-[36px] border border-slate-200 bg-[linear-gradient(135deg,rgba(15,23,42,0.98),rgba(15,23,42,0.88))] px-6 py-10 text-white shadow-2xl sm:px-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-teal-200">Ready to launch</p>
          <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight">Connect learners to authentication, diagnostics, and roadmaps in one smooth flow.</h2>
          <p className="mt-3 max-w-2xl text-base leading-8 text-slate-300">
            Start with the landing page, then step straight into the product experience with the backend already doing the hard work.
          </p>
        </div>

        <Button onClick={onStart} className="min-w-[200px] bg-white text-slate-950 hover:bg-slate-100">
          Go to Auth
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </section>
  );
}
