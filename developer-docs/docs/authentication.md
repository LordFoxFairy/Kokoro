# Authentication and service context

Kokoro API v1 is a server-to-server Product API. A trusted server adapter supplies service identity, credential, namespace, and principal context. Browser code must not hold service credentials or call the BFF directly.

The executable examples use conspicuously fake environment values and a local fixture server. Never commit or embed a deployed credential in documentation, client bundles, logs, or source control.
