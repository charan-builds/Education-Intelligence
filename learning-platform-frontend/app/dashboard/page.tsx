import ClientRouteRedirect from "@/components/routing/ClientRouteRedirect";

export const dynamic = "force-dynamic";

export default function DashboardIndexPage() {
  return <ClientRouteRedirect fallbackPath="/auth" useRoleRedirect />;
}
