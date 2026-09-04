# Cancel a run

Send `run.cancel` to the control operation for the session and run.

<<< ../../examples/curl/cancel-run.sh{bash}

The `202` control receipt means the cancellation command was admitted. Continue reading the AG-UI stream or session snapshot until the run becomes terminal. A run that finishes before cancellation is observed remains terminal; a network timeout alone is not evidence that cancellation failed.

Retry an uncertain cancel with the same idempotency key and body.
