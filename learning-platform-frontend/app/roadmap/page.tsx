import React from "react";

import ClientRouteRedirect from "@/components/routing/ClientRouteRedirect";

export const dynamic = "force-dynamic";

export default function RoadmapIndexPage() {
  return <ClientRouteRedirect fallbackPath="/student/roadmap" />;
}
