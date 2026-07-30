# Kokoro Kubernetes release shape

`base/` is the latest-only production shape corresponding to Root Compose. It is intentionally small
(`replicas: 1`) so a default integration cluster does not waste resources; release overlays may scale
each stateless process independently after its SLO evidence exists.

## Contents

- `infra.yaml`: PostgreSQL 18, Redis, Mongo replica set, MinIO, and LiteLLM. Replace these with managed
  services by changing workload URLs, not the application topology.
- `runtime-config.yaml`: non-secret Platform database/role identity only.
- `jobs.yaml`: the one-shot `platform-migrator` Job. No business seed Job exists.
- `platform.yaml`: Platform API, Admission, Authorization, asset data plane, model gateway, worker,
  typed Admin, Hub management HTTP, and Hub runtime Connect.
- `app.yaml`: Session, Agent worker, Agent evidence provider, and one independent Site release image.
- `overlays/kind`: changes only the shared workspace access mode for a one-node cluster.

## Required Secrets

`kokoro-infra-env` is generated from the gitignored `deploy/.env.prod` for local infrastructure only.
Application credentials are external workload-specific Secrets. Create them through the cluster secret
manager before applying workloads:

| Workload | Environment Secret | File Secret |
|---|---|---|
| Platform migrator | `platform-migrator-environment` | none |
| Platform runtimes | `platform-<role>-environment` | `platform-<role>-files` |
| Hub management | `hub-http-environment` | `hub-http-files` |
| Hub runtime | `hub-runtime-environment` | `hub-runtime-files` |
| Session | `session-environment` | `session-files` |
| Agent worker | `agent-worker-environment` | `agent-worker-files` |
| Agent evidence | `agent-evidence-environment` | `agent-evidence-files` |
| Site release | `site-release-environment` | `site-release-files` |

For a fresh database only, create `platform-admin-authority-bootstrap-file` with one key named
`admin-authority-bootstrap.json`, apply `bootstrap/admin-authority-job.yaml` after the migrator, wait
for completion, and delete both the Job and Secret. The document must define 2–16 distinct governors;
the database transition is one-way (`open` to `sealed`). This Job is intentionally absent from `base/`.

Every Platform environment Secret exposes its own value as `DATABASE_URL_PLATFORM`; no runtime Pod
receives `DATABASE_URL_PLATFORM_MIGRATOR`. File keys are mounted at `/run/secrets/kokoro` and env paths
must match the filenames. Peer registries and certificates must use the service DNS identities shown in
the manifests. Session's Service deliberately exposes browser `3900` and owner authority `3901`; Agent
evidence is a separate mTLS Service on `8443`.

## Images and Site isolation

Replace the four local image names in a release overlay with verified digests: `kokoro-platform`,
`kokoro-session`, `kokoro-agent`, and `kokoro-site-release`. The last image comes from one generated Site
repository. Deploy another Site as another Deployment/image/host binding; do not add runtime `siteId`
switching to the existing Site Pod.

## Render and apply

```bash
kubectl kustomize --load-restrictor LoadRestrictionsNone deploy/k8s/base >/dev/null
kubectl kustomize --load-restrictor LoadRestrictionsNone deploy/k8s/base | kubectl apply -f -
kubectl -n kokoro wait --for=condition=complete --timeout=15m job/platform-migrator
kubectl -n kokoro get deploy,service,pod
```

Apply the migration Job before admitting traffic, then perform the one-time Admin authority step on a
fresh install. Business configuration then goes through typed control-plane APIs; it is not a
Kubernetes Job. Secure Connect services use TCP readiness in this base
because kubelet cannot present the workload mTLS identity; production overlays should replace it with a
mesh or dedicated authenticated readiness probe.

The Kind overlay uses `ReadWriteOnce` only because every Pod is scheduled on one node. Cloud deployments
must provide RWX storage or move workspace/package storage to S3. Stopping or rolling workloads never
deletes PVCs, buckets, images, or developer data.
