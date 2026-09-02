# Historical Credit contract slice

This directory is retained only for migration archaeology and compatibility
review. Credit is not an active Root wire surface and `kokoro-credit` is not an
active repository or runtime. The production owner is `kokoro-billing`, whose
PostgreSQL-backed HTTP contract is the only current Billing API authority.

The archived Proto, consumer manifest, buf configuration and tests are kept
together so they cannot be mistaken for the active `contract/` toolchain.
