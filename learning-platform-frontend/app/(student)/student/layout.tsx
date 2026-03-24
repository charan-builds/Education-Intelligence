import type { PropsWithChildren } from "react";

import WorkspaceShell from "@/components/layouts/WorkspaceShell";
import { studentNav } from "@/components/layouts/navigation";

export default function StudentLayout({ children }: PropsWithChildren) {
  return (
    <WorkspaceShell
      allowedRoles={["student"]}
      roleLabel="Student"
      navigation={studentNav}
      searchPlaceholder="Search roadmap steps, topics, or mentor guidance"
    >
      {children}
    </WorkspaceShell>
  );
}
