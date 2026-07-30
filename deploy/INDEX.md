---
architectureIndex: 1
rootId: root.deploy
owners:
  - "@LordFoxFairy"
---

# Deployment entrypoints

## Responsibilities

Own Root-facing deployment examples and provisioning entrypoints that compose independently released service artifacts.

## Non-responsibilities

This directory does not build child artifacts, own service migrations, or replace Root Infra lifecycle policy.

## Public boundary

[`README.md`](README.md) plus `provision.sh` (single-host bring-up), `.env.example` (single-host interpolation and configuration template), `storage.yaml` and `storage.s3.yaml` (workspace backend examples), and `k8s/` — `base/` holds `namespace`/`runtime-config`/`infra`/`platform`/`app`/`jobs` manifests behind `base/kustomization.yaml`, with `overlays/kind/` as the only committed overlay. Production Compose may split the master template through its per-process `KOKORO_*_ENV_FILE` inputs; Kubernetes requires workload-specific Secrets.

## Callers and dependencies

Operators consume released child images and Root-managed configuration; child repositories do not import this directory. `provision.sh` brings up infra first, then runs the migration job, then the app tier — the root `docker-compose.app.yml` attaches to the external `kokoro-net` network and connects to every backend by URL rather than starting a second infra stack.

## Data ownership and events

Deployment configuration contains examples only. Runtime databases, buckets, secrets, and event streams remain service-owned.

## Runtime and security

Examples use fail-loud placeholders and `.env.example` is the only committed single-host env template. Real secrets must come from the deployment environment or a secret manager and must never be committed. File credentials mount only into their owning process. Every backend is injected as a URL, so pointing at managed cloud services is an env change, not a topology change.

## Idempotency, failure, and recovery

Provisioning must converge declared resources and fail loudly. Rollback selects previously verified artifacts and Root pin combinations.

## Extension rules and forbidden dependencies

Add environment-neutral deployment composition here. Keep service-specific build and migration logic in the owning child repository.

## Current gotchas

These files are not production certification evidence; Wave 9 still requires canary, rollback, on-call, and disaster-recovery proof.

## Verification

Run `node --test scripts/infra/*.test.mjs`, then render without applying: `docker compose --env-file deploy/.env.example -f docker-compose.app.yml config` and `kubectl kustomize --load-restrictor LoadRestrictionsNone deploy/k8s/overlays/kind`. Never render real secret values into logs or committed receipts.
