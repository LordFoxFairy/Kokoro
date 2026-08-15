SET search_path TO kokoro, pg_catalog;

CREATE TABLE capability_runtime_snapshot (
  snapshot_id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  scope_key text NOT NULL,
  digest bytea NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT capability_runtime_snapshot_organization_fk
    FOREIGN KEY (organization_id)
    REFERENCES iam_organization(organization_id) ON DELETE RESTRICT,
  CONSTRAINT capability_runtime_snapshot_scope_digest_key
    UNIQUE (organization_id, scope_key, digest),
  CONSTRAINT capability_runtime_snapshot_snapshot_scope_key
    UNIQUE (snapshot_id, scope_key),
  CONSTRAINT capability_runtime_snapshot_scope_key_ck
    CHECK (length(scope_key) BETWEEN 1 AND 255)
);

CREATE TABLE capability_command_receipt (
  receipt_id uuid PRIMARY KEY,
  command_id uuid NOT NULL,
  command_kind text NOT NULL,
  request_digest bytea NOT NULL,
  status text NOT NULL,
  result_ref text,
  result_payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT capability_command_receipt_command_key UNIQUE (command_id),
  CONSTRAINT capability_command_receipt_command_kind_ck
    CHECK (command_kind = 'ResolveRuntimeSnapshot'),
  CONSTRAINT capability_command_receipt_status_ck
    CHECK (status IN ('processing','completed','failed')),
  CONSTRAINT capability_command_receipt_result_payload_ck CHECK (
    result_payload IS NULL OR jsonb_typeof(result_payload) IN ('object','array')
  )
);

CREATE FUNCTION capability_reject_snapshot_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW IS NOT DISTINCT FROM OLD THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'runtime snapshot is immutable'
    USING ERRCODE='23514', CONSTRAINT='capability_runtime_snapshot_immutable_ck';
END;
$$;

CREATE TRIGGER capability_runtime_snapshot_immutable_trigger
BEFORE UPDATE OR DELETE ON capability_runtime_snapshot
FOR EACH ROW EXECUTE FUNCTION capability_reject_snapshot_update();

CREATE FUNCTION capability_reject_receipt_claim_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.command_id IS DISTINCT FROM OLD.command_id
    OR NEW.command_kind IS DISTINCT FROM OLD.command_kind
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
  THEN
    RAISE EXCEPTION 'capability command receipt claim is immutable'
      USING ERRCODE='23514', CONSTRAINT='capability_command_receipt_claim_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER capability_command_receipt_claim_immutable_trigger
BEFORE UPDATE OF command_id, command_kind, request_digest ON capability_command_receipt
FOR EACH ROW EXECUTE FUNCTION capability_reject_receipt_claim_update();
