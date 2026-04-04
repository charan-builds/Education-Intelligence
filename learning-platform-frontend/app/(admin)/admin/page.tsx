import { redirect } from "next/navigation";

import { appRoutes } from "@/utils/appRoutes";

export default function AdminHomePage() {
  redirect(appRoutes.admin.dashboard);
}
