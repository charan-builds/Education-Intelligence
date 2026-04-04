import { redirect } from "next/navigation";

import { appRoutes } from "@/utils/appRoutes";

export default function StudentHomePage() {
  redirect(appRoutes.student.dashboard);
}
