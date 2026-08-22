import type { SiteBindingVerifier } from "../../modules/runtime-manifest/ports.js";
import type { TenantRequestContext } from "../../modules/runtime-manifest/model.js";

export class IamSiteBindingClient implements SiteBindingVerifier {
  public constructor(private readonly baseUrl: string, private readonly backendToken: string) {}
  public async verify(input: Readonly<{ context: TenantRequestContext; requestedSiteId: string; host: string }>): Promise<void> {
    const url = new URL("/internal/iam/site-binding", `${this.baseUrl}/`);
    url.searchParams.set("site_id", input.requestedSiteId);
    url.searchParams.set("host", input.host.replace(/:\d+$/u, "").toLowerCase());
    const response = await fetch(url, { headers: { authorization: `Bearer ${this.backendToken}` } });
    if (!response.ok) throw new Error("IAM site binding rejected");
    const body = await response.json() as { data?: { tenantId?: string; siteId?: string } };
    if (body.data?.tenantId !== input.context.tenantId || body.data.siteId !== input.requestedSiteId) throw new Error("IAM site binding rejected");
  }
}
