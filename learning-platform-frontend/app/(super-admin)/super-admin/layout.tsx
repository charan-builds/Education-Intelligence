import type { PropsWithChildren } from "react";

import WorkspaceShell from "@/components/layouts/WorkspaceShell";
import { superAdminNav } from "@/components/layouts/navigation";

export default function SuperAdminLayout({ children }: PropsWithChildren) {
  return (
    <WorkspaceShell
      allowedRoles={["super_admin"]}
      roleLabel="Super Admin"
      navigation={superAdminNav}
      searchPlaceholder="Search tenants, outbox events, or platform health"
    >
      {children}
    </WorkspaceShell>
  );
}
