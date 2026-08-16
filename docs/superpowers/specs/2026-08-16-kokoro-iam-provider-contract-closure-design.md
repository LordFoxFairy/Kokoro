---
artifact: design-specification
version: "1.0"
created: 2026-08-16
status: approved-design-awaiting-written-review
owner: kokoro-iam
promotion_target: kokoro-iam/docs
---

# Kokoro IAM Provider Contract Closure Design

## 1. Purpose

Close the two provider defects that prevent `kokoro-iam` and Admin Web from proving the complete
organization membership and live RBAC journeys:

1. non-add Member mutations do not atomically bind the requested Organization to the Member; and
2. the administration surface cannot evaluate a selected User's current organization permission
   without changing the meaning of caller authorization.

This specification is a parent-repository review artifact. After written approval, its requirements
are incorporated into the IAM-owned PRD, technical design, implementation plan, and P0 test catalog.
The parent copy is then removed so there is one current authority in `kokoro-iam`.

## 2. Current Evidence

The accepted provider candidate is
`c96e369d3f04f1ae653da16fec3c83266484c9bc`. Repository acceptance passed for the cases encoded by
that candidate, but Admin Web pair analysis found that its contract cannot prove the intended P0
semantics:

- `ChangeMemberRole`, `SuspendMember`, `ReactivateMember`, `RemoveMember`, and `RestoreMember` accept
  only `member_id` after their command context;
- `Authorize` evaluates the authenticated caller, while Admin Web callers are admitted as platform
  administrators; and
- `IssueAccessToken(organization_id)` requires the caller to be an active Member, so it cannot be
  used to impersonate or inspect a selected User and would exclude global administrators from
  Organizations where they are not Members.

Passing tests against those contracts are insufficient evidence for organization-bound mutations or
the grant-allow-revoke-deny acceptance criterion. A new provider candidate and fresh acceptance run
are required.

## 3. Scope

### 3.1 In scope

- bind every non-add Member mutation to `organization_id` from RPC through command digest,
  application service, repository port, PostgreSQL transaction, audit event, and result;
- add an administrator-only `InspectUserAuthorization` RPC that evaluates one selected User against
  current organization RBAC state;
- retain `Authorize` as caller authorization for Web and backend workloads;
- extend unit, application, integration, contract, security, and admin tests;
- generate a new IAM repository acceptance report and frozen provider handoff; and
- expose enough provider behavior for Admin Web to prove organization isolation and immediate RBAC
  revocation in its own browser acceptance.

### 3.2 Out of scope

- generalized principal, subject, actor, or polymorphic ownership tables;
- dynamic role or permission authoring;
- target-session impersonation or token exchange;
- a second browser authentication framework;
- SQL schema changes, foreign keys, cascades, or relationship validation triggers;
- compatibility branches for the old provider contract; and
- Admin Web implementation or browser evidence inside the IAM repository.

## 4. Selected Design

Use two explicit contracts:

1. organization-scoped Member commands for mutation; and
2. a separate administrator inspection method for evaluating a selected User.

This keeps command authorization, caller authorization, and administrative inspection distinct.
`Authorize` remains narrow and cannot silently switch from evaluating the caller to evaluating a
request field. `InspectUserAuthorization` is not impersonation: the authenticated administrator
remains the actor, the selected User is only the evaluation target, and no target Session is created
or accepted.

### 4.1 Rejected alternatives

**Optional `user_id` on `Authorize`.** Rejected because one method would have two authorization
meanings. Field omission, caller class, and workload admission would combine into a fragile privilege
boundary, and existing consumers could accidentally evaluate a different User.

**Effective-permission list only.** Rejected because a list does not prove the exact decision for a
permission and optional resource reference. It also encourages clients to cache a permission set
instead of requesting a current decision.

**Organization access token for the selected User.** Rejected because token issuance requires a
real active Session and Member and would turn inspection into impersonation. It also cannot represent
suspended, removed, deleted, or cross-organization targets that must return a denial.

## 5. RPC Contract

### 5.1 Organization-bound Member commands

Add required UUID fields without reusing existing Protobuf field numbers:

| Request | New field |
|---|---|
| `ChangeMemberRoleRequest` | `string organization_id = 4` |
| `SuspendMemberRequest` | `string organization_id = 3` |
| `ReactivateMemberRequest` | `string organization_id = 3` |
| `RemoveMemberRequest` | `string organization_id = 3` |
| `RestoreMemberRequest` | `string organization_id = 3` |

Protovalidate applies `string.uuid = true`. An omitted field therefore fails at the RPC boundary.
The provider does not infer Organization scope from the Member and does not retain a fallback path
for the old request shape. Preserving occupied field numbers is Protobuf correctness, not legacy
compatibility.

Every canonical command digest includes `organization_id` in addition to the existing mutation
fields. Reusing a `command_id` with another Organization produces `command_digest_mismatch` and no
state change.

### 5.2 Administrator authorization inspection

Add this method to `IamAuthorizationService`:

```proto
message InspectUserAuthorizationRequest {
  string request_id = 1 [(buf.validate.field).string.uuid = true];
  string organization_id = 2 [(buf.validate.field).string.uuid = true];
  string user_id = 3 [(buf.validate.field).string.uuid = true];
  string permission_key = 4 [(buf.validate.field).string = {
    pattern: "^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$",
    max_len: 128
  }];
  optional string resource_ref = 5 [(buf.validate.field).string.max_len = 320];
}

message InspectUserAuthorizationResponse {
  bool allowed = 1;
  string reason_code = 2;
  string user_id = 3;
  string organization_id = 4;
  repeated string role_keys = 5;
  uint64 authorization_version = 6;
  google.protobuf.Timestamp evaluated_at = 7;
}

rpc InspectUserAuthorization(InspectUserAuthorizationRequest)
    returns (InspectUserAuthorizationResponse);
```

Validation matches `Authorize`: UUIDs are required, permission keys use the code-owned key pattern
and 128-character bound, and `resource_ref` is optional with a 320-character bound.

The response intentionally has no target `session_id`. The result identifies the evaluated User and
Organization and reports only current role keys. The authenticated administrator's identity remains
in request context and structured log/trace fields, not in the evaluation result.

### 5.3 Admission and authorization

- only the `admin-web` workload may call `InspectUserAuthorization`;
- the authenticated actor must have an active, unexpired IAM Session;
- the actor's User must be active and have `platform_role=admin` at evaluation time;
- caller identity and platform-admin scope come only from authenticated handler context; and
- request `user_id` is never treated as the caller or used to issue a token.

Missing, expired, revoked, suspended, deleted, or demoted administrator state returns the existing
opaque authentication or permission error. Workload and actor checks run before target evaluation.

## 6. Application Boundaries

### 6.1 Member mutation input

`OrganizationApplicationService` and `OrganizationRepository` require `organizationId` for all five
non-add Member operations. No overload or optional field preserves the old shape.

The application layer validates UUID and role-key syntax before invoking the repository. The
repository remains responsible for transactional existence, lifecycle, ownership, and relationship
checks.

### 6.2 Inspection input

`AuthorizationApplicationService.inspectUserAuthorization()` accepts:

```text
actor
organizationId
userId
permissionKey
resourceRef?
```

The `AuthorizationRepository` exposes a separate `inspectUserAuthorization` operation. It does not
add optional target semantics to `authorize` or reuse an `ActorContext` for the selected User.

## 7. Transaction Semantics

### 7.1 Member mutations

Each command executes in one SERIALIZABLE transaction with the existing bounded retry for SQLSTATE
`40001` and `40P01`:

```text
BEGIN SERIALIZABLE
claim or replay command receipt using digest that includes organization_id
lock requested Organization
authorize the authenticated actor against the requested Organization
load and lock Member by {id: member_id, organizationId: organization_id}
load and lock the current or requested Role in the same Organization when applicable
re-read lifecycle state and last-owner invariant
apply one mutation
append SecurityEvent containing requested organization_id and member_id
complete CommandReceipt
COMMIT
```

The repository never loads a Member globally and compares Organization scope after mutation. If the
pair does not match, it returns the same nondisclosing `not_found` result used for an inaccessible
Member and performs no write, event append, or completed mutation receipt.

Deterministic lock order remains Organization, then User/Member/Role UUID order. Last-owner checks
run after the Organization and relevant Member rows are locked. Restore validates the same
Organization pair and original business identifiers inside the transaction.

### 7.2 Authorization inspection

Inspection runs in one REPEATABLE READ transaction so User, Organization, Member, Role, Permission,
and RolePermission are evaluated from one PostgreSQL snapshot:

```text
validate current administrator User and Session
load active requested Organization
load selected User
load active Member by {organization_id, user_id}
load active Role constrained to the same organization_id
load active Permission and unrevoked RolePermission
return one current decision and composite authorization_version
```

No target row is mutated or locked for write. A selected User with no active membership in the
requested Organization returns `allowed=false` with `reason_code=membership_inactive`; it does not
fall back to a membership from another Organization.

Inspection emits the existing bounded request log and trace dimensions for the administrator actor,
selected User, Organization, permission key, result, and duration. It does not append a
`SecurityEvent` inside the read transaction. Member mutations continue to append their durable
SecurityEvents in the same SERIALIZABLE write transaction.

The decision changes immediately after a committed role change, suspension, removal, User or
Organization lifecycle change, Role retirement, Permission retirement, or RolePermission revocation.

## 8. Error and Disclosure Rules

| Condition | Result |
|---|---|
| malformed request field | `INVALID_ARGUMENT` with safe field path |
| invalid administrator Session/User | existing opaque `UNAUTHENTICATED` shape |
| authenticated non-admin actor | `PERMISSION_DENIED` |
| Member does not belong to requested Organization | nondisclosing `NOT_FOUND` |
| command ID reused with another Organization/digest | `command_digest_mismatch` |
| selected User inactive | decision `allowed=false`, `user_inactive` |
| Organization or membership inactive | decision `allowed=false`, `membership_inactive` |
| permission unknown or retired | decision `allowed=false`, `permission_unknown` |
| active membership lacks permission | decision `allowed=false`, `permission_denied` |

RPC errors never expose SQL, constraint names, stack traces, raw credentials, or whether a Member ID
exists in another Organization. Inspection decisions expose only fields required by the authorized
platform administration workflow.

## 9. Persistence and SQL

No schema or migration change is required. Existing scalar relationship IDs, business UNIQUE
constraints, row-local CHECK constraints, and indexes remain authoritative. The implementation adds
no FK, cascade, relationship trigger, compatibility table, or preservation ledger.

Relationship correctness remains application-transaction behavior. Integration tests must inspect
SQL state after cross-organization and idempotency failures to prove that no Member, command result,
or SecurityEvent was incorrectly written.

## 10. Test Design

The IAM-owned P0 catalog is amended before production code. Existing cases remain; focused cases are
added or strengthened in these categories:

### Unit

- permission-key and inspection-input validation;
- canonical command digest changes when `organization_id` changes; and
- authorization decision/version construction contains no target Session.

### Application

- each Member mutation forwards and requires `organization_id`;
- wrong-Organization Member commands return nondisclosing not found;
- inspection distinguishes allowed, permission denied, membership inactive, user inactive, and
  unknown permission; and
- caller authorization and selected-User inspection remain separate operations.

### Integration

- real PostgreSQL rejects all five wrong-Organization Member commands without state or audit change;
- command ID reuse across Organizations returns digest mismatch without mutation;
- parent Organization soft delete racing a Member command has one legal final state;
- last-owner mutation and restore invariants remain correct with the explicit Organization scope;
- grant/allow then role change, suspension, removal, and revocation each produce immediate denial;
  and
- inspection reads no membership or role from another Organization.

### Contract

- generated descriptors contain the exact new fields and method;
- Protovalidate rejects missing or malformed Organization/User IDs;
- a generated client interoperates with a real listener for every changed RPC;
- old Member request shapes fail validation rather than entering a fallback; and
- non-admin workloads cannot invoke inspection.

### Security

- a normal Web or backend caller cannot inspect another User;
- a demoted, suspended, deleted, expired, or revoked administrator cannot inspect;
- cross-Organization Member IDs do not disclose target existence; and
- logs and error details contain no credentials, token material, or raw request payloads.

### Admin

- a platform administrator selects Organization, User, and permission and receives the exact current
  decision;
- Member role/lifecycle commands and inspection results correlate to the requested Organization; and
- structured request logs identify the real administrator actor and selected User separately, while
  Member mutation SecurityEvents continue to record the administrator as actor.

No new case may be skipped, marked todo, retried by the acceptance runner, or satisfied only by an
in-memory repository when PostgreSQL/RPC evidence is required.

## 11. Acceptance and Evidence

After implementation, `kokoro-iam` creates a clean candidate and runs its repository-owned
acceptance from a fresh PostgreSQL database. The report records:

- local and UTC start/finish time and timezone offset;
- repository commit, tree, dirty state, Proto hash, migration hash, and catalog hash;
- classified JUnit and coverage output;
- fresh schema proof with zero foreign keys and zero disallowed triggers;
- real listener RPC evidence for every changed method;
- SQL and structured-log evidence for organization mismatch, idempotency, concurrency, and live
  authorization transitions; and
- overall IAM repository decision.

Only a passing, clean candidate may be published to Admin Web. Admin Web imports the exact provider
commit/tree/hashes and owns its BFF tests, UI tests, production build, runtime smoke, and two visible
Chromium rounds. Those rounds must perform every business step through the browser and archive
screenshots, trace, video, HAR, RPC, SQL, logs, timestamps, and checksums. They may not replace a
browser action with a direct RPC or database shortcut.

IAM imports only the final approved pair-result reference, not Web browser artifacts or a central
system-test repository.

## 12. Documentation Promotion

After written review approval:

1. update `kokoro-iam/docs/product/PRD-001-standard-iam.md` with the explicit organization-bound
   command and administrator inspection requirements;
2. update `kokoro-iam/docs/architecture/standard-iam-technical-design.md` with this contract,
   transaction, error, and evidence design;
3. append a focused implementation task to the IAM-owned implementation plan;
4. update `kokoro-iam/test/catalog/p0.yaml` before production code;
5. update adjacent `INDEX.md` files and the Admin Web pair contract; and
6. remove this parent-repository process file in the same promotion sequence so no duplicate current
   authority remains.

## 13. Definition of Done

The IAM provider closure is complete only when all of the following are true:

- every non-add Member mutation requires and transactionally enforces `organization_id`;
- command idempotency binds that Organization scope;
- `InspectUserAuthorization` is administrator-only and evaluates current selected-User RBAC without
  impersonation or a generalized subject model;
- caller `Authorize` behavior remains unchanged;
- all classified IAM tests and static/build gates pass fresh;
- a new clean IAM acceptance candidate and immutable report are committed;
- Admin Web can import the exact candidate without a compatibility path; and
- the parent draft is removed after the finalized documents live in `kokoro-iam`.
