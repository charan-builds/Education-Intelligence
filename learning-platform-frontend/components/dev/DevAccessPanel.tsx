"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Copy, KeyRound, ShieldEllipsis, X } from "lucide-react";
import { useEffect, useState } from "react";

import Button from "@/components/ui/Button";

const devAccounts = [
  { tenant: "Demo University", tenantId: "1", email: "student@example.com", password: "Student123!" },
  { tenant: "Demo University", tenantId: "1", email: "teacher@example.com", password: "Teacher123!" },
  { tenant: "Demo University", tenantId: "1", email: "mentor@example.com", password: "Mentor123!" },
  { tenant: "Demo University", tenantId: "1", email: "admin@example.com", password: "admin123" },
  { tenant: "Platform", tenantId: "platform", email: "superadmin@platform.example.com", password: "SuperAdmin123!" },
  { tenant: "Northwind School", tenantId: "northwind", email: "student@northwind.local", password: "Student123!" },
  { tenant: "Acme Learning Co", tenantId: "acme", email: "student@acme.local", password: "Student123!" },
];

export default function DevAccessPanel() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "d") {
        event.preventDefault();
        setIsEnabled(true);
        setIsOpen((current) => !current);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  async function copyLine(value: string, label: string) {
    await navigator.clipboard.writeText(value);
    setCopied(label);
    window.setTimeout(() => setCopied((current) => (current === label ? null : current)), 1600);
  }

  return (
    <>
      <AnimatePresence>
        {isEnabled ? (
          <motion.button
            type="button"
            initial={{ opacity: 0, scale: 0.8, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 16 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-5 right-5 z-[70] flex h-12 w-12 items-center justify-center rounded-full border border-white/40 bg-slate-950 text-white shadow-2xl backdrop-blur-xl"
            aria-label="Open developer access panel"
          >
            <ShieldEllipsis className="h-5 w-5" />
          </motion.button>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen ? (
          <>
            <motion.div
              className="fixed inset-0 z-[79] bg-slate-950/60 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              className="fixed inset-x-4 top-[8vh] z-[80] mx-auto max-w-3xl rounded-[32px] border border-white/30 bg-[rgba(15,23,42,0.92)] p-6 text-white shadow-[0_30px_100px_rgba(2,6,23,0.45)]"
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.98 }}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.3em] text-teal-200">Developer Access</p>
                  <h2 className="mt-2 text-2xl font-semibold">Demo credentials and tenant references</h2>
                  <p className="mt-2 text-sm text-slate-300">Visible only after pressing `Ctrl + Shift + D`. Keep this panel for development and demos only.</p>
                </div>
                <button type="button" onClick={() => setIsOpen(false)} className="rounded-2xl border border-white/10 p-2 text-slate-300">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="mt-6 grid gap-3">
                {devAccounts.map((account) => {
                  const line = `${account.email} / ${account.password} / tenant ${account.tenantId}`;
                  const label = `${account.email}-${account.tenantId}`;
                  return (
                    <div key={label} className="rounded-[24px] border border-white/10 bg-white/5 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold">{account.tenant}</p>
                          <p className="mt-1 text-xs uppercase tracking-[0.22em] text-slate-400">Tenant {account.tenantId}</p>
                        </div>
                        <Button variant="ghost" className="text-white hover:bg-white/10" onClick={() => copyLine(line, label)}>
                          <Copy className="h-4 w-4" />
                          {copied === label ? "Copied" : "Copy"}
                        </Button>
                      </div>
                      <div className="mt-4 grid gap-2 text-sm text-slate-200 md:grid-cols-[1.4fr_1fr_auto]">
                        <p className="truncate">{account.email}</p>
                        <p>{account.password}</p>
                        <p className="inline-flex items-center gap-2 text-teal-200">
                          <KeyRound className="h-4 w-4" />
                          {account.tenantId}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </>
        ) : null}
      </AnimatePresence>
    </>
  );
}
