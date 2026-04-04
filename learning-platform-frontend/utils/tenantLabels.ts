import type { TenantType } from "@/types/tenant";

export function formatTenantTypeLabel(type: TenantType | string): string {
  switch (type) {
    case "platform":
      return "Platform";
    case "college":
      return "College";
    case "company":
      return "Company";
    case "school":
      return "School";
    case "personal":
      return "Personal Workspace";
    default:
      return String(type)
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
  }
}

export function describeTenantAudience(type: TenantType | string): string {
  switch (type) {
    case "platform":
      return "Platform-wide operations";
    case "college":
      return "Institutional higher-ed workspace";
    case "school":
      return "K-12 or school workspace";
    case "company":
      return "Enterprise or workforce learning workspace";
    case "personal":
      return "Independent learner self-serve workspace";
    default:
      return "Learning workspace";
  }
}
