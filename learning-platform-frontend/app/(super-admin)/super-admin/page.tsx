import { redirect } from "next/navigation";

import { appRoutes } from "@/utils/appRoutes";

export default function SuperAdminHomePage() {
  redirect(appRoutes.superAdmin.dashboard);
}
