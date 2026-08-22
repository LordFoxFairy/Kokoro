import { createHash } from "node:crypto";
import type { ManifestCache, SiteBindingVerifier, SystemRepository } from "./ports.js";
import type { RuntimeManifest, TenantRequestContext } from "./model.js";

function cacheKey(context: TenantRequestContext, productId: string, locale: string): string {
  return `manifest:${context.tenantId}:${context.siteId ?? "global"}:${productId}:${locale}`;
}
export class RuntimeManifestService {
  public constructor(private readonly repository: SystemRepository, private readonly cache: ManifestCache, private readonly binding: SiteBindingVerifier) {}
  public async get(input: Readonly<{ context: TenantRequestContext; siteId: string; productId: string; locale: string; host: string }>): Promise<RuntimeManifest> {
    await this.binding.verify({ context: input.context, requestedSiteId: input.siteId, host: input.host });
    const key = cacheKey(input.context, input.productId, input.locale);
    const cached = await this.cache.get(key);
    if (cached !== null) return cached;
    const manifest = await this.repository.getManifest({ context: input.context, productId: input.productId, locale: input.locale });
    await this.cache.set(key, manifest, 30);
    return manifest;
  }
}
export function manifestDigest(value: unknown): string { return createHash("sha256").update(JSON.stringify(value)).digest("hex"); }
