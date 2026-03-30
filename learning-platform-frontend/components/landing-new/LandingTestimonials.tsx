import { Quote, Star } from "lucide-react";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { testimonials, trustBadges } from "@/components/landing-new/content";

export default function LandingTestimonials() {
  return (
    <section id="testimonials" className="relative py-28">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="Testimonials"
          title="Loved by"
          accent="ambitious teams"
          description="The visual refresh ships with the same stable app underneath, which is exactly what these customers care about."
          icon={Quote}
        />

        <div className="mt-16 grid gap-8 lg:grid-cols-3">
          {testimonials.map((testimonial) => (
            <article
              key={testimonial.name}
              className="relative rounded-[2rem] border-2 border-slate-200 bg-white/80 p-8 shadow-2xl backdrop-blur-xl"
            >
              <Quote className="absolute right-6 top-6 h-14 w-14 text-slate-200" />
              <div className="flex items-center gap-4">
                <div className={`flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${testimonial.gradientClassName} text-lg font-bold text-white shadow-lg`}>
                  {testimonial.avatar}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{testimonial.name}</h3>
                  <p className="text-sm text-slate-600">{testimonial.role}</p>
                </div>
              </div>
              <div className="mt-5 flex gap-1">
                {[0, 1, 2, 3, 4].map((star) => (
                  <Star key={star} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="mt-5 text-base leading-8 text-slate-700">&ldquo;{testimonial.quote}&rdquo;</p>
              <div className="mt-6 inline-flex rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">
                {testimonial.result}
              </div>
            </article>
          ))}
        </div>

        <div className="mt-16 rounded-[2rem] border-2 border-slate-200 bg-white/80 p-10 text-center shadow-2xl backdrop-blur-xl">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Trusted by leading institutions</p>
          <div className="mt-8 grid gap-6 sm:grid-cols-3 lg:grid-cols-5">
            {trustBadges.map((badge) => (
              <div key={badge} className="text-2xl font-bold text-slate-400 transition hover:text-slate-700">
                {badge}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
