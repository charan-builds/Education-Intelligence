import { redirect } from "next/navigation";

import { appRoutes } from "@/utils/appRoutes";

export default function TeacherHomePage() {
  redirect(appRoutes.teacher.dashboard);
}
