import { apiClient } from "@/services/apiClient";
import type {
  EcosystemOverview,
  MarketplaceListing,
  PluginDefinition,
  PublicApiClient,
  SubscriptionPlan,
  TenantSubscription,
} from "@/types/ecosystem";

export async function getEcosystemOverview(): Promise<EcosystemOverview> {
  const { data } = await apiClient.get<EcosystemOverview>("/ecosystem/overview");
  return data;
}

export async function getMarketplaceListings(): Promise<MarketplaceListing[]> {
  const { data } = await apiClient.get<MarketplaceListing[]>("/ecosystem/marketplace");
  return data;
}

export async function getPlugins(): Promise<PluginDefinition[]> {
  const { data } = await apiClient.get<PluginDefinition[]>("/ecosystem/plugins");
  return data;
}

export async function getApiClients(): Promise<PublicApiClient[]> {
  const { data } = await apiClient.get<PublicApiClient[]>("/ecosystem/api-clients");
  return data;
}

export async function getSubscriptionPlans(): Promise<SubscriptionPlan[]> {
  const { data } = await apiClient.get<SubscriptionPlan[]>("/ecosystem/subscription-plans");
  return data;
}

export async function createPlugin(payload: {
  key: string;
  name: string;
  plugin_type: string;
  provider: string;
  version: string;
  config_json: string;
}): Promise<PluginDefinition> {
  const { data } = await apiClient.post<PluginDefinition>("/ecosystem/plugins", payload);
  return data;
}

export async function createApiClient(payload: {
  name: string;
  scopes: string[];
  rate_limit_per_minute: number;
}): Promise<PublicApiClient> {
  const { data } = await apiClient.post<PublicApiClient>("/ecosystem/api-clients", payload);
  return data;
}

export async function createSubscriptionPlan(payload: {
  code: string;
  name: string;
  monthly_price_cents: number;
  usage_price_cents: number;
  features: string[];
}): Promise<SubscriptionPlan> {
  const { data } = await apiClient.post<SubscriptionPlan>("/ecosystem/subscription-plans", payload);
  return data;
}

export async function assignSubscription(payload: { plan_id: number; seats: number }): Promise<TenantSubscription> {
  const { data } = await apiClient.post<TenantSubscription>("/ecosystem/subscription", payload);
  return data;
}
