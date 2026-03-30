import { Activity } from "lucide-react";

import LandingSectionHeading from "@/components/landing-new/LandingSectionHeading";
import { liveFeed, metricCards } from "@/components/landing-new/content";

export default function LandingMetrics() {
  return (
    <section className="relative py-28">
      <div className="absolute inset-0 opacity-30">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(251,191,36,0.14) 1px, transparent 1px), linear-gradient(to bottom, rgba(251,191,36,0.14) 1px, transparent 1px)",
            backgroundSize: "56px 56px",
          }}
        />
      </div>
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <LandingSectionHeading
          badge="Live Metrics"
          title="The numbers"
          accent="speak"
          description="The homepage now showcases the SaaS value proposition with stable, hydration-safe data and reusable section components."
          icon={Activity}
        />

        <div className="mt-16 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {metricCards.map((metric) => (
            <article
              key={metric.label}
              className={`rounded-[2rem] border-2 border-slate-200 bg-gradient-to-br ${metric.tintClassName} p-8 shadow-xl`}
            >
              <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${metric.gradientClassName} shadow-lg`}>
                <metric.icon className="h-7 w-7 text-white" />
              </div>
              <div className={`mt-6 text-4xl font-bold bg-gradient-to-r ${metric.gradientClassName} bg-clip-text text-transparent`}>{metric.value}</div>
              <div className="mt-2 text-sm font-medium text-slate-700">{metric.label}</div>
            </article>
          ))}
        </div>

        <div className="mt-10 rounded-[2rem] border-2 border-slate-200 bg-white/80 p-8 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-2xl font-bold text-slate-900">Live Activity</h3>
              <p className="text-sm text-slate-600">A preview of real-time product energy</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-xl border border-emerald-300 bg-emerald-100 px-4 py-2 text-sm font-semibold text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Live updates
            </div>
          </div>

          <div className="mt-6 space-y-3">
            {liveFeed.map((item) => (
              <div key={`${item.user}-${item.action}`} className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br ${item.gradientClassName} text-sm font-bold text-white`}>
                  {item.user.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="text-sm text-slate-900">
                    <span className="font-semibold">{item.user}</span> <span className="text-slate-600">{item.action}</span>
                  </div>
                  <div className="text-xs text-slate-500">{item.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
