import type { PropsWithChildren } from "react";

import WorkspaceShell from "@/components/layouts/WorkspaceShell";
import { teacherNav } from "@/components/layouts/navigation";

export default function TeacherLayout({ children }: PropsWithChildren) {
  return (
    <WorkspaceShell
      allowedRoles={["teacher", "mentor", "admin", "super_admin"]}
      roleLabel="Teacher"
      navigation={teacherNav}
      searchPlaceholder="Search learners, cohort signals, or mastery insights"
    >
      {children}
    </WorkspaceShell>
  );
}
