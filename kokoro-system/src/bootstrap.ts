import { MysqlPool } from "./infrastructure/mysql/client.js";
import { RedisCoordinator } from "./infrastructure/redis/coordinator.js";
import { MysqlSystemRepository } from "./modules/runtime-manifest/mysql-repository.js";
import { RuntimeManifestService } from "./modules/runtime-manifest/service.js";
import type { SiteBindingVerifier } from "./modules/runtime-manifest/ports.js";
export async function createSystemRuntime(input: Readonly<{ databaseUrl: string; redisUrl: string; redisNamespace: string; binding: SiteBindingVerifier }>) {
  const pool = new MysqlPool(input.databaseUrl);
  const redis = new RedisCoordinator(input.redisUrl, input.redisNamespace);
  await redis.assertReady();
  return { pool, redis, service: new RuntimeManifestService(new MysqlSystemRepository(pool), redis, input.binding) };
}
