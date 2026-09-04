# Webhooks

Webhooks are not part of the Kokoro public v1 contract. The canonical OpenAPI currently defines neither an outbound webhook object nor a registration, delivery, or signature-verification operation.

Do not implement a receiver against an internal owner callback, copy a private signing header, or assume a signature algorithm. When BFF publishes a webhook surface, the owner contract must first define registration, event envelopes, delivery identity, replay behavior, timestamp tolerance, key rotation, and signature verification. The generated reference and this guide will then be updated together.

For current Agent progress, use the [AG-UI event stream](../concepts/ag-ui).
