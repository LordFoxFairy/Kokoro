# Frozen contract consumer inventory

`consumer-inventory.json` is the Root fail-closed inventory for every approved
cross-repository call edge. It records the owner contract pin, consumer-side
evidence. The former Web-to-IAM direct-call violation is preserved only in historical checkpoints, not the current inventory.

## Evidence model

- `owner.repository_commit` must equal the gitlink object ID in the Root Git
  index. `owner.contract_sha256` is the SHA-256 of `contract_path` read from
  that exact child commit blob with `git show`; it is never calculated from a
  child working tree.
- For OpenAPI and HTTP-event edges, `owner.contract_version` must equal the
  frozen contract's `info.version`. The verifier reads JSON or the canonical
  top-level `info.version` YAML header and fails closed on missing metadata.
- Every `evidence`, `version_assertions` and `producer_runtime_assertion`
  digest is likewise calculated from the referenced child commit blob. Dirty
  or newer child working-tree content and local Git replace refs are not
  evidence for a frozen edge.
- The edge target is the runtime receiver; `owner` identifies the repository
  that owns the canonical contract and can therefore differ from the target.
  Event protocols are producer-owned: Scheduler owns its outbound dispatch
  schema while BFF is the receiving consumer and runtime evidence. The retired
  direct Scheduler→Agent edge remains only in historical checkpoints.
- `code_generator_version` and `runtime_package_version` describe the frozen
  consumer implementation. The literal `unmanaged` is permitted only on a
  `broken` edge. Every active edge has exactly one consumer runtime assertion;
  an active generated edge also has exactly one generator assertion. The
  exemptions are limited to `EDGE-BROWSER-WEB` with
  `not-applicable:same-origin-route` and the Agent→System handwritten HTTP edge
  with `not-applicable:handwritten-agent-system-http`.
- Only Agent→System, Agent→Storage and Agent→Capability use the `uv-lock`
  assertion. It proves the editable Agent project resolves a unique, direct
  registry runtime dependency: `httpx` for System and `connectrpc` for
  Storage and Platform. The System edge also pins its handwritten client and receipt, and checks that
  the receipt, both POST operations, and all source digests agree with the
  System owner's committed OpenAPI and provenance. This does not waive any
  other edge's generator or runtime evidence.
- The two Agent Connect edges use `agent-connect-codegen`: exact generator
  version and all vendored generation input blobs, plus Storage combined
  provenance or Platform's codegen configuration. The existing Agent
  checker verifies generated Python bytes and independent profiles.
- Only `EDGE-CAPABILITY-IAM` can use `npm-file-archive`. The generator
  assertion still reads the exact IAM owner's `sdk/package.json`. The runtime
  assertion binds the installed Capability file package to the verified clean
  IAM archive digest and the owner's committed OpenAPI, configuration, and lock.
  It checks embedded provenance, consumer runtime importer, archive resolution
  and SRI, and the owner's exact direct dependency resolutions. No other edge
  gains a file archive exception.
- `npm-package-json` assertions read the canonical dependency pointer from
  `package.json`. A consumer Node runtime may instead use
  `plain-version-file`: its path is exactly `.node-version`, its package is
  `node`, and both the declaration and file contain one exact semantic
  version, such as `node@22.22.2`.
- Every active `http-event` edge additionally has one singular
  `producer_runtime_assertion`. It must reference the canonical contract
  owner's repository and commit, and never replaces the consumer assertions.
  W0B producer assertions accept only `go-mod`: its path is exactly `go.mod`,
  its package is `go`, and the blob contains exactly one canonical
  `go X.Y.Z` directive matching a declaration such as `go@1.26.8`.
- `violations` are known calls outside the approved topology. Their presence
  intentionally keeps the real compatibility CLI red until the call and its
  inventory entry are removed together with the verifier baseline update.

## Owner-first update protocol

1. Change and verify the contract in its owner repository.
2. Commit and push the owner change before updating any consumer pin.
3. Update the consumer from the published owner artifact, including generated
   code and runtime integration, then commit and push the consumer evidence.
4. Update this inventory from the new Root gitlinks and exact commit blobs.
5. Change an edge to `active` only when the contract, runtime, generated client,
   frozen evidence and tests all agree. A partial update remains `broken`.
6. Run the focused tests and the real compatibility CLI. A red result is the
   expected current baseline only when its complete error set is the declared
   broken edges plus recorded illegal edges, with no schema, gitlink, digest,
   evidence or version drift.

## Commands and exit semantics

```bash
python3 -m pytest \
  scripts/tests/test_contract_compatibility.py \
  scripts/tests/test_contract_checkpoint.py -q
python3 scripts/verify-contract-compatibility.py \
  --inventory verification/contracts/consumer-inventory.json
python3 scripts/verify-contract-checkpoint.py \
  --expected verification/contracts/checkpoints/task-a-scheduler-bff-only.json
```

The focused tests return exit code `0` when verifier behavior is sound. The
real CLI returns `0` only when every edge is active and no violation remains;
the current Task A composition returns `1` because it declares two broken
edges, with thirteen active and no illegal edge. Earlier
checkpoints remain historical snapshots, not the current composition gate.
The checkpoint CLI compares the complete active/broken/illegal ID sets with
the selected checkpoint, runs the same compatibility verifier, and returns
`0` only when every non-success outcome is
the broken or illegal outcome declared by that checkpoint. Counts alone do not
pass, and schema, gitlink, digest, evidence or version drift remains fatal.
