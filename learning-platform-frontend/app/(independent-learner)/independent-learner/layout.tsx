import type { PropsWithChildren } from "react";

import WorkspaceShell from "@/components/layouts/WorkspaceShell";
import { independentLearnerNav } from "@/components/layouts/navigation";

export default function IndependentLearnerLayout({ children }: PropsWithChildren) {
  return (
    <WorkspaceShell
      allowedRoles={["independent_learner"]}
      roleLabel="Independent Learner"
      navigation={independentLearnerNav}
      searchPlaceholder="Search goals, roadmap steps, topics, or mentor guidance"
    >
      {children}
    </WorkspaceShell>
  );
}
