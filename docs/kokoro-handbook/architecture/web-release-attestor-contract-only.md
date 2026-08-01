---
architectureIndex: 1
rootId: web.release-attestor
owners:
  - "@LordFoxFairy"
---

# Web release attestor (contract-only)

## Responsibilities

This boundary names the future non-human Kokoro Web workload that may submit signed web artifact provenance to the Site publication authority. It is deliberately separate from the user Site and Admin operator boundaries. The manifest locates the boundary beside the Site build tooling so its repository ownership is explicit; this entry does not claim that the current scaffold package implements the attestor.

## Non-responsibilities

It does not authorize candidates, approve certification, publish a SiteRelease, activate a release, handle user traffic, or exercise Admin operator authority. It does not own Platform publication data or signing trust policy.

## Public boundary

The only declared entrypoint is `SiteEvidenceAdmissionService.RecordReleaseEvidence` in the [Root publication contract](../../../contract/proto/kokoro/platform/site/v1/site_publication.proto). The registry lifecycle is `contract-only`: there is no registered runtime provider or admitted producer deployment in R0a.

## Callers and dependencies

The future caller is an attested build/release workload in `kokoro-web`. It consumes the Root-owned evidence-admission contract and calls the Platform-owned Site publication authority. Browser, `web.user`, and `web.admin` identities are forbidden callers.

## Data ownership and events

The workload may produce immutable compiled-manifest and artifact-provenance evidence. Platform owns evidence admission, candidate association, certification, SiteRelease publication, and all durable publication records.

## Runtime and security

Admission requires a workload identity, fixed audience, registered producer identity and revision, fixed provenance-attestor role, workload-attestation revision, artifact digest, and verified DSSE provenance. Human operator session fields are intentionally absent. The workload cannot use its identity to authorize, certify, publish, or activate a release.

## Idempotency, failure, and recovery

Submissions use a stable command identity and immutable candidate binding. Retries must preserve the same identity and payload digest; ambiguous outcomes reconcile through the durable command receipt. Failed admission never advances certification, release publication, or the active pointer.

## Extension rules and forbidden dependencies

Add runtime code only in a dedicated non-browser build-control package and register its exact producer trust material before changing this lifecycle from contract-only. Never place signing keys in the Site scaffold, browser bundle, Admin session, generated project, or artifact itself. Never grant this boundary operator or lifecycle authority.

## Current gotchas

`kokoro-web/packages/site-scaffold` is presently only the nearest repository ownership anchor for build tooling. Its existing packaging and local qualification behavior is not the evidence producer, is not a trust registration, and is not proof of a deployed attestor.

## Verification

Run `node scripts/contract/check-boundary-registry.mjs`, the generated-contract checks, and the web release composition checker. R0b must add provider implementation, generated consumer mirror, producer registration, and live end-to-end evidence before the lifecycle may leave contract-only.
