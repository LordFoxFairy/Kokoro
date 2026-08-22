export type ScopeType = "global" | "tenant" | "site" | "product" | "surface";
export type TenantRequestContext = Readonly<{ tenantId: string; siteId: string | null; actorId: string | null; correlationId: string }>;
export type RuntimeManifest = Readonly<{
  tenantId: string; siteId: string; productId: string; locale: string;
  navigation: readonly unknown[]; localeNamespaces: readonly unknown[]; theme: Readonly<Record<string, unknown>>;
  featureFlags: readonly unknown[]; references: readonly unknown[];
  configVersion: string; releaseId: string | null; digest: string;
}>;
export type ConfigRecord = Readonly<{
  id: string; moduleKey: string; scopeType: ScopeType; scopeId: string | null; productId: string | null;
  configKey: string; schemaVersion: number; value: unknown; status: "active" | "deleted";
  configVersion: bigint; releaseId: string | null; digest: string;
}>;
