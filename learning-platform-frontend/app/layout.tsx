import type { Metadata } from "next";

import "./globals.css";
import "reactflow/dist/style.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Learnova AI",
  description: "Production-ready AI learning SaaS frontend with a premium landing page, role-based dashboards, and FastAPI integration readiness.",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-[family:var(--font-body)] text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
