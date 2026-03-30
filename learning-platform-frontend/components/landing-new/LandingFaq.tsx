"use client";

import { ChevronDown, HelpCircle } from "lucide-react";
import { useState } from "react";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { faqItems } from "@/components/landing-new/content";

export default function LandingFaq() {
  const [openQuestion, setOpenQuestion] = useState(faqItems[0]?.question ?? "");

  return (
    <section className="relative py-28">
      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="FAQ"
          title="Answers for a"
          accent="safe rollout"
          description="The integration preserves the existing app contract and keeps homepage concerns isolated."
          icon={HelpCircle}
        />

        <div className="mt-14 space-y-4">
          {faqItems.map((item) => {
            const isOpen = item.question === openQuestion;

            return (
              <article key={item.question} className="rounded-[1.75rem] border-2 border-slate-200 bg-white/80 p-6 shadow-lg backdrop-blur-xl">
                <button
                  type="button"
                  onClick={() => setOpenQuestion(isOpen ? "" : item.question)}
                  className="flex w-full items-center justify-between gap-4 text-left"
                >
                  <span className="text-lg font-semibold text-slate-900">{item.question}</span>
                  <ChevronDown className={`h-5 w-5 flex-none text-slate-500 transition ${isOpen ? "rotate-180" : ""}`} />
                </button>
                {isOpen ? <p className="mt-4 text-base leading-8 text-slate-600">{item.answer}</p> : null}
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
