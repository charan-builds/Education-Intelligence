const journey = [
  {
    step: "Authenticate",
    description: "Sign in through the existing auth system and establish a secure session with the FastAPI backend.",
  },
  {
    step: "Run diagnostic",
    description: "Start a diagnostic for a selected goal, answer questions one at a time, and submit when the test is complete.",
  },
  {
    step: "Review roadmap",
    description: "Fetch the latest roadmap, inspect progress, and identify the highest-priority next topics.",
  },
];

export default function LandingJourney() {
  return (
    <section className="mx-auto grid max-w-6xl gap-8 rounded-[36px] border border-slate-200/80 bg-white/80 p-6 shadow-panel backdrop-blur-xl lg:grid-cols-[0.95fr_1.05fr] lg:p-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-orange-600">Product Journey</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Clean, intentional flow from discovery to action.</h2>
        <p className="mt-4 text-base leading-8 text-slate-600">
          The frontend is organized around the exact workflow your backend already supports. That keeps the UI scalable and keeps the data model honest.
        </p>
      </div>

      <div className="space-y-4">
        {journey.map((item, index) => (
          <div key={item.step} className="rounded-[28px] border border-slate-200 bg-slate-50/90 p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-sm font-semibold text-white">
                {index + 1}
              </div>
              <h3 className="text-lg font-semibold text-slate-950">{item.step}</h3>
            </div>
            <p className="mt-3 text-sm leading-7 text-slate-600">{item.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
