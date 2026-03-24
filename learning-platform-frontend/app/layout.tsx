import type { Metadata } from "next";

import "./globals.css";
import "reactflow/dist/style.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Learning Intelligence Platform",
  description: "Multi-tenant learning intelligence platform with role-based dashboards and AI-assisted workflows",
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
