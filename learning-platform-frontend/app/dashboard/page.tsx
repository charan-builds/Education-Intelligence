"use client";

import ClientRouteRedirect from "@/components/routing/ClientRouteRedirect";
import { appRoutes } from "@/utils/appRoutes";

export default function DashboardPage() {
  return <ClientRouteRedirect fallbackPath={appRoutes.auth} useRoleRedirect />;
}
