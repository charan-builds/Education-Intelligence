import type { PropsWithChildren } from "react";

import WorkspaceShell from "@/components/layouts/WorkspaceShell";
import { adminNav } from "@/components/layouts/navigation";

export default function AdminLayout({ children }: PropsWithChildren) {
  return (
    <WorkspaceShell
      allowedRoles={["admin", "super_admin"]}
      roleLabel="Admin"
      navigation={adminNav}
      searchPlaceholder="Search users, content, community, or flags"
    >
      {children}
    </WorkspaceShell>
  );
}
