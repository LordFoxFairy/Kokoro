## Slice A machine authority

`slice-a-contract-manifest.yaml` is a byte-for-byte installed copy of the reviewed Root design authority. The additive projection-NACK revision preserves the existing `AckProjection` method and positive wire while adding presence-aware request fields 6–7 and exact durable response echoes 3–4. Run:

    python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml

before rendering or generation. The validator is dependency-free and fail-closed. Proto/OpenAPI and declared consumer closures are rendered or generated only from this authority; child repositories never edit or copy it manually.

Generation keeps provenance honest in two commits. First commit this source authority, renderer output, registry and tests. From that exact clean source SHA, generate Root `root-e2e` with `contract/generate.py --consumer root-e2e --repo .` into a descendant-output commit; Agent and Chat regenerate their own declared closures from the same SHA. A dirty worktree SHA is never written into generated headers or `provenance.json`.
