import type { Metadata } from "next";
import { Inter } from "next/font/google";

import "./globals.css";
import "reactflow/dist/style.css";
import Providers from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

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
      <body className={`${inter.variable} font-[family:var(--font-body)] text-foreground`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
