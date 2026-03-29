import { Activity, LockKeyhole, Route, ServerCog } from "lucide-react";

const features = [
  {
    title: "Backend-backed diagnostics",
    description: "Questions, answers, scoring, and roadmap triggers are all powered by the production FastAPI backend.",
    icon: Activity,
  },
  {
    title: "JWT-authenticated sessions",
    description: "The frontend uses a shared Axios client with bearer-token injection and route protection across the core flow.",
    icon: LockKeyhole,
  },
  {
    title: "Guided learner journey",
    description: "From first click to roadmap review, each page is focused on one clear action so users always know what to do next.",
    icon: Route,
  },
  {
    title: "SaaS-ready architecture",
    description: "Docker, Redis, Celery, PostgreSQL, and observability are already in place behind the scenes.",
    icon: ServerCog,
  },
];

export default function LandingFeatureGrid() {
  return (
    <section className="mx-auto max-w-6xl px-2">
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-teal-700">Why Learnova</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">A frontend built around a real backend, not a mock story.</h2>
        <p className="mt-3 max-w-3xl text-base leading-8 text-slate-600">
          The product flow is intentionally simple: authenticate, assess skill gaps, and review a roadmap generated from your diagnostic results.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {features.map((feature) => (
          <article key={feature.title} className="story-card min-h-[220px]">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
              <feature.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-5 text-xl font-semibold text-slate-950">{feature.title}</h3>
            <p className="mt-3 text-sm leading-7 text-slate-600">{feature.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
