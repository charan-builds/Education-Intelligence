export type MarketplaceListing = {
  id: number;
  tenant_id: number;
  teacher_user_id: number;
  topic_id?: number | null;
  resource_id?: number | null;
  listing_type: string;
  title: string;
  summary: string;
  price_cents: number;
  currency: string;
  is_published: boolean;
  average_rating: number;
  review_count: number;
  created_at: string;
};

export type PluginDefinition = {
  id: number;
  tenant_id: number;
  key: string;
  name: string;
  plugin_type: string;
  provider: string;
  version: string;
  config_json: string;
  is_enabled: boolean;
  created_at: string;
};

export type PublicApiClient = {
  id: number;
  tenant_id: number;
  name: string;
  client_key: string;
  scopes: string[];
  rate_limit_per_minute: number;
  created_at: string;
};

export type SubscriptionPlan = {
  id: number;
  tenant_id?: number | null;
  code: string;
  name: string;
  monthly_price_cents: number;
  usage_price_cents: number;
  features: string[];
  is_active: boolean;
  created_at: string;
};

export type TenantSubscription = {
  id: number;
  tenant_id: number;
  plan_id: number;
  status: string;
  seats: number;
  monthly_usage_units: number;
  current_period_end: string;
  created_at: string;
};

export type EcosystemOverview = {
  marketplace_listing_count: number;
  published_course_count: number;
  plugin_count: number;
  api_client_count: number;
  active_subscription?: TenantSubscription | null;
  monetization_snapshot: {
    marketplace_gmv_cents: number;
    subscription_mrr_cents: number;
    active_plan?: string | null;
  };
};
