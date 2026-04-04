import { redirect } from "next/navigation";

import { appRoutes } from "@/utils/appRoutes";

export default function IndependentLearnerHomePage() {
  redirect(appRoutes.independentLearner.dashboard);
}
