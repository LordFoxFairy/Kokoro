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

[`README.md`](README.md), `provision.sh`, storage examples, and `k8s/` are the operator-facing boundary.

## Callers and dependencies

Operators consume released child images and Root-managed configuration; child repositories do not import this directory.

## Data ownership and events

Deployment configuration contains examples only. Runtime databases, buckets, secrets, and event streams remain service-owned.

## Runtime and security

Examples use fake values. Real secrets must come from the deployment environment or a secret manager and must never be committed.

## Idempotency, failure, and recovery

Provisioning must converge declared resources and fail loudly. Rollback selects previously verified artifacts and Root pin combinations.

## Extension rules and forbidden dependencies

Add environment-neutral deployment composition here. Keep service-specific build and migration logic in the owning child repository.

## Current gotchas

These files are not production certification evidence; Wave 9 still requires canary, rollback, on-call, and disaster-recovery proof.

## Verification

Run Root Infra policy tests and render the relevant deployment configuration without production credentials.
