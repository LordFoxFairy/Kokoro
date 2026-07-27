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

[`README.md`](README.md) plus `provision.sh` (single-host bring-up), `.env.example` (the one env contract both compose files consume), `storage.yaml` and `storage.s3.yaml` (workspace backend examples), and `k8s/` — `base/` holds `namespace`/`infra`/`platform`/`app`/`jobs` manifests behind `base/kustomization.yaml`, with `overlays/kind/` as the only committed overlay.

## Callers and dependencies

Operators consume released child images and Root-managed configuration; child repositories do not import this directory. `provision.sh` brings up infra first, then runs the migration job, then the app tier — the root `docker-compose.app.yml` attaches to the external `kokoro-net` network and connects to every backend by URL rather than starting a second infra stack.

## Data ownership and events

Deployment configuration contains examples only. Runtime databases, buckets, secrets, and event streams remain service-owned.

## Runtime and security

Examples use fake values and `.env.example` is the only committed env template. Real secrets must come from the deployment environment or a secret manager and must never be committed. Every backend is injected as a URL, so pointing at managed cloud services is an env change, not a topology change.

## Idempotency, failure, and recovery

Provisioning must converge declared resources and fail loudly. Rollback selects previously verified artifacts and Root pin combinations.

## Extension rules and forbidden dependencies

Add environment-neutral deployment composition here. Keep service-specific build and migration logic in the owning child repository.

## Current gotchas

These files are not production certification evidence; Wave 9 still requires canary, rollback, on-call, and disaster-recovery proof.

## Verification

Run `node --test scripts/infra/*.test.mjs`, then render without applying: `docker compose -f docker-compose.app.yml config` and `kubectl kustomize deploy/k8s/overlays/kind`. Never render against production credentials.
