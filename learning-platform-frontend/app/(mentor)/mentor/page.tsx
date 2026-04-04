import { redirect } from "next/navigation";

import { appRoutes } from "@/utils/appRoutes";

export default function MentorHomePage() {
  redirect(appRoutes.mentor.dashboard);
}
