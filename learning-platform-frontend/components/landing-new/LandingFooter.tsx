import { Brain } from "lucide-react";
import Link from "next/link";

import { footerIcons, footerLinks } from "@/components/landing-new/content";

type LandingFooterProps = {
  dashboardHref: string;
};

export default function LandingFooter({ dashboardHref }: LandingFooterProps) {
  return (
    <footer className="relative overflow-hidden pb-16 pt-10">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-[2.2rem] border-2 border-slate-200 bg-white/80 p-8 shadow-2xl backdrop-blur-xl sm:p-10">
          <div className="grid gap-12 lg:grid-cols-[1.2fr_0.8fr_0.8fr_0.8fr]">
            <div>
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-yellow-400 to-amber-500 shadow-lg">
                  <Brain className="h-7 w-7 text-white" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-slate-900">Learnova AI</div>
                  <div className="text-sm text-slate-500">Premium education intelligence</div>
                </div>
              </div>
              <p className="mt-6 max-w-sm text-base leading-8 text-slate-600">
                The homepage is now visually upgraded, while the existing SaaS routes and auth infrastructure remain intact behind it.
              </p>
              <div className="mt-6 flex gap-3">
                {footerIcons.map((item) => (
                  <div
                    key={item.label}
                    className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm"
                    aria-label={item.label}
                    title={item.label}
                  >
                    <item.icon className="h-5 w-5" />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-900">Product</h3>
              <ul className="mt-5 space-y-3">
                {footerLinks.product.map((link) => (
                  <li key={link} className="text-sm text-slate-600">
                    {link}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-900">Resources</h3>
              <ul className="mt-5 space-y-3">
                {footerLinks.resources.map((link) => (
                  <li key={link} className="text-sm text-slate-600">
                    {link}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-900">Company</h3>
              <ul className="mt-5 space-y-3">
                {footerLinks.company.map((link) => (
                  <li key={link} className="text-sm text-slate-600">
                    {link}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-10 flex flex-col gap-4 border-t border-slate-200 pt-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <p>© 2026 Learnova AI. All rights reserved.</p>
            <div className="flex flex-wrap gap-4">
              <Link href="/auth?mode=login" className="transition hover:text-slate-900">
                Login
              </Link>
              <Link href="/auth?mode=register" className="transition hover:text-slate-900">
                Register
              </Link>
              <Link href={dashboardHref} className="transition hover:text-slate-900">
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
