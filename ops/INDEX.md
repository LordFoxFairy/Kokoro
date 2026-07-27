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

[`README.md`](README.md) and each dependency's explicit example configuration are the supported operator boundary.

## Callers and dependencies

Operators may enable these dependencies through approved deployment composition. Product code consumes only declared remote protocols.

## Data ownership and events

Optional dependencies own their own local volumes when enabled; Kokoro service records and event streams remain outside this tree.

## Runtime and security

Only example configuration is committed. Credentials, cookies, and production telemetry payloads must not enter Git or verification output.

## Idempotency, failure, and recovery

An optional dependency failure must degrade according to its product policy and must not corrupt Kokoro business transactions.

## Extension rules and forbidden dependencies

Add operational examples here only when ownership and protocol boundaries are explicit. Do not create in-process imports from services.

## Current gotchas

The presence of an example does not mean the dependency is enabled in every Site profile.

## Verification

Validate configuration syntax through the owning Root Infra or deployment gate before enabling a profile.
