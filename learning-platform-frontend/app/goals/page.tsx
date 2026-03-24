import ClientRouteRedirect from "@/components/routing/ClientRouteRedirect";

export const dynamic = "force-dynamic";

export default function GoalsIndexPage() {
  return <ClientRouteRedirect fallbackPath="/goals/select" />;
}
