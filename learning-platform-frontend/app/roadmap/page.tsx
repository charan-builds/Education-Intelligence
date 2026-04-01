"use client";

import ClientRouteRedirect from "@/components/routing/ClientRouteRedirect";
import { appRoutes } from "@/utils/appRoutes";

export default function RoadmapPage() {
  return <ClientRouteRedirect fallbackPath={appRoutes.student.roadmap} />;
}
