import type { PropsWithChildren } from "react";

import WorkspaceShell from "@/components/layouts/WorkspaceShell";
import { mentorNav } from "@/components/layouts/navigation";

export default function MentorLayout({ children }: PropsWithChildren) {
  return (
    <WorkspaceShell
      allowedRoles={["student", "teacher", "mentor", "admin", "super_admin"]}
      roleLabel="Mentor"
      navigation={mentorNav}
      searchPlaceholder="Search mentor recommendations, notifications, or weak topics"
    >
      {children}
    </WorkspaceShell>
  );
}
