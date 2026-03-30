import { ArrowRight, LayoutDashboard } from "lucide-react";
import Link from "next/link";

type LandingFinalCtaProps = {
  dashboardHref: string;
  isAuthenticated: boolean;
};

export default function LandingFinalCta({ dashboardHref, isAuthenticated }: LandingFinalCtaProps) {
  return (
    <section className="relative py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-yellow-400 to-amber-500 p-2 shadow-2xl shadow-yellow-500/25">
          <div className="rounded-[2.2rem] bg-white px-8 py-14 sm:px-12 lg:px-20 lg:py-20">
            <div className="inline-flex items-center gap-2 rounded-full border-2 border-yellow-300 bg-yellow-100 px-4 py-2 text-sm font-semibold text-slate-900">
              Limited Time Offer
            </div>
            <h2 className="mt-8 text-4xl font-bold leading-tight text-slate-950 sm:text-5xl lg:text-6xl">
              Ready to transform <span className="bg-gradient-to-r from-yellow-600 to-amber-600 bg-clip-text text-transparent">your learning?</span>
            </h2>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
              Join the premium homepage experience with the same reliable dashboards, auth flows, and product capabilities already built into the app.
            </p>

            <div className="mt-8 flex flex-wrap gap-4 text-sm font-medium text-slate-700">
              {["14-day free trial", "No credit card needed", "Cancel anytime", "Full access to core features"].map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="h-6 w-6 rounded-full bg-emerald-500" />
                  {item}
                </div>
              ))}
            </div>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              {isAuthenticated ? (
                <Link
                  href={dashboardHref}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-8 py-4 text-base font-bold text-white shadow-xl transition hover:bg-slate-900"
                >
                  <LayoutDashboard className="h-5 w-5" />
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/register"
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-yellow-400 to-amber-500 px-8 py-4 text-base font-bold text-white shadow-xl transition hover:from-yellow-500 hover:to-amber-600"
                  >
                    Get Started
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                  <Link
                    href="/login"
                    className="inline-flex items-center justify-center rounded-2xl border-2 border-slate-200 bg-white px-8 py-4 text-base font-bold text-slate-900 shadow-lg transition hover:bg-slate-50"
                  >
                    Login
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
