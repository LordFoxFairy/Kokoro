## Slice A machine authority

`slice-a-contract-manifest.yaml` is a byte-for-byte installed copy of the reviewed Root design authority. Run:

    python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml

before rendering or generation. The validator is dependency-free and fail-closed. This commit does not yet render Proto/OpenAPI; the next independently reviewed JIT cut does that. Child repositories never edit or copy this file manually.
