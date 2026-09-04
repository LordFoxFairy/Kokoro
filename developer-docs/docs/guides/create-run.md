# Create a run

Submit a message to an existing session context. The path session ID and returned run ID are opaque.

<<< ../../examples/curl/create-run.sh{bash}

## Handle the receipt

Expect `202 Accepted` with `data.run_id`, `data.user_message_id`, `data.assistant_message_id`, and `meta.request_id`. Save all four before opening the event stream.

Use one idempotency key for this logical submission. A timeout does not justify a new key: retry the identical request with the original key so the server can replay the first receipt instead of starting duplicate work.

Continue with [replay after disconnect](./replay-after-disconnect).
