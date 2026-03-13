export type TenantType = "platform" | "college" | "company" | "school";

export type Tenant = {
  id: number;
  name: string;
  type: TenantType;
  created_at: string;
};

export type PageMeta = {
  total: number;
  limit: number;
  offset: number;
  next_offset: number | null;
  next_cursor: string | null;
};

export type TenantPageResponse = {
  items: Tenant[];
  meta: PageMeta;
};

export type CreateTenantPayload = {
  name: string;
  type: TenantType;
};
