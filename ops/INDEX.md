---
architectureIndex: 1
rootId: root.ops
owners:
  - "@LordFoxFairy"
---

# Optional operations dependencies

## Responsibilities

Own local examples for optional operational dependencies such as Langfuse and SearXNG.

## Non-responsibilities

This directory does not own Kokoro product services, business state, provider credentials, or the Root Infra lifecycle.

## Public boundary

[`README.md`](README.md) plus two example stacks: `langfuse/docker-compose.yml` with `langfuse/.env.local.example` (LLM tracing), and `searxng/settings.yml` (search backend). No script here is executable automation; operators copy and adapt.

## Callers and dependencies

Operators may enable these dependencies through approved deployment composition. Product code reaches them only over their declared remote HTTP endpoints. Langfuse shares the Root Infra Redis and MinIO and keeps its own Postgres and ClickHouse.

## Data ownership and events

Optional dependencies own their own local volumes when enabled; Kokoro service records and event streams remain outside this tree.

## Runtime and security

Only example configuration is committed. `langfuse/.env.local.example` carries placeholder values only — real keys come from the deployment environment. Credentials, cookies, and production telemetry payloads must not enter Git or verification output.

## Idempotency, failure, and recovery

N/A — this root holds example configuration with no runtime of its own. Degradation and retry belong to the enabling deployment composition and to the consuming service's own policy.

## Extension rules and forbidden dependencies

Add operational examples here only when ownership and protocol boundaries are explicit. Do not create in-process imports from services.

## Current gotchas

The presence of an example does not mean the dependency is enabled in every Site profile.

## Verification

Run `git diff --check`, then `docker compose -f ops/langfuse/docker-compose.yml config` to render the stack without starting it. Do not point either example at production credentials.
