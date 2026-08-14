SET search_path TO kokoro, pg_catalog;

CREATE TABLE agent_run (
  agent_run_id uuid PRIMARY KEY,
  launch_id uuid NOT NULL,
  launch_request_digest bytea NOT NULL,
  namespace text NOT NULL,
  execution_manifest_id uuid,
  state text NOT NULL,
  epoch bigint NOT NULL DEFAULT 1,
  next_event_seq bigint NOT NULL DEFAULT 1,
  generation bigint NOT NULL DEFAULT 1,
  terminal_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_run_launch_key UNIQUE (launch_id),
  CONSTRAINT agent_run_run_launch_key UNIQUE (agent_run_id, launch_id),
  CONSTRAINT agent_run_run_namespace_key UNIQUE (agent_run_id, namespace),
  CONSTRAINT agent_run_state_ck CHECK (
    state IN (
      'preparing','queued','running','awaiting_input',
      'completed','failed','cancelled','admission_failed'
    )
  ),
  CONSTRAINT agent_run_epoch_ck CHECK (epoch > 0),
  CONSTRAINT agent_run_next_event_seq_ck CHECK (next_event_seq > 0),
  CONSTRAINT agent_run_generation_ck CHECK (generation > 0)
);

CREATE TABLE agent_execution_manifest (
  execution_manifest_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  namespace text NOT NULL,
  digest bytea NOT NULL,
  agent_preset_key text NOT NULL,
  agent_preset_digest bytea NOT NULL,
  model_revision_id uuid NOT NULL,
  capability_snapshot_id uuid NOT NULL,
  usage_mode text NOT NULL,
  usage_policy_digest bytea NOT NULL,
  usage_authorization_ref text,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_execution_manifest_run_key UNIQUE (agent_run_id),
  CONSTRAINT agent_execution_manifest_manifest_run_key
    UNIQUE (execution_manifest_id, agent_run_id),
  CONSTRAINT agent_execution_manifest_run_namespace_fk
    FOREIGN KEY (agent_run_id, namespace)
    REFERENCES agent_run(agent_run_id, namespace) ON DELETE RESTRICT,
  CONSTRAINT agent_execution_manifest_usage_mode_ck
    CHECK (usage_mode IN ('unmetered','metered')),
  CONSTRAINT agent_execution_manifest_usage_authorization_ck CHECK (
    (usage_mode = 'unmetered' AND usage_authorization_ref IS NULL)
    OR (usage_mode = 'metered' AND usage_authorization_ref IS NOT NULL)
  ),
  CONSTRAINT agent_execution_manifest_payload_ck
    CHECK (jsonb_typeof(payload) = 'object')
);

ALTER TABLE agent_run
  ADD CONSTRAINT agent_run_execution_manifest_fk
  FOREIGN KEY (execution_manifest_id, agent_run_id)
  REFERENCES agent_execution_manifest(execution_manifest_id, agent_run_id)
  DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE agent_run_lease (
  agent_run_id uuid PRIMARY KEY,
  worker_id text NOT NULL,
  lease_token_hash bytea NOT NULL,
  leased_until timestamptz NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  CONSTRAINT agent_run_lease_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_run_lease_generation_ck CHECK (generation > 0)
);

CREATE TABLE agent_control_inbox (
  control_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  command_id uuid NOT NULL,
  request_digest bytea NOT NULL,
  command_schema_version integer NOT NULL,
  command_payload jsonb NOT NULL,
  interrupt_fingerprint bytea,
  status text NOT NULL,
  applied_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_control_inbox_run_command_key UNIQUE (agent_run_id, command_id),
  CONSTRAINT agent_control_inbox_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_control_inbox_status_ck
    CHECK (status IN ('pending','applied','rejected','failed')),
  CONSTRAINT agent_control_inbox_command_schema_version_ck
    CHECK (command_schema_version > 0),
  CONSTRAINT agent_control_inbox_command_payload_ck CHECK (
    jsonb_typeof(command_payload) = 'object'
    AND octet_length(command_payload::text) <= 65536
  ),
  CONSTRAINT agent_control_inbox_interrupt_fingerprint_ck CHECK (
    interrupt_fingerprint IS NULL OR octet_length(interrupt_fingerprint) = 32
  ),
  CONSTRAINT agent_control_inbox_applied_at_ck CHECK (
    (status = 'applied' AND applied_at IS NOT NULL)
    OR (status <> 'applied' AND applied_at IS NULL)
  )
);

CREATE TABLE agent_event_outbox (
  event_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  epoch bigint NOT NULL,
  seq bigint NOT NULL,
  kind text NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  published_at timestamptz,
  acked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_event_outbox_run_seq_key UNIQUE (agent_run_id, seq),
  CONSTRAINT agent_event_outbox_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_event_outbox_epoch_ck CHECK (epoch > 0),
  CONSTRAINT agent_event_outbox_seq_ck CHECK (seq > 0),
  CONSTRAINT agent_event_outbox_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT agent_event_outbox_payload_ck
    CHECK (jsonb_typeof(payload) IN ('object','array'))
);

CREATE INDEX agent_event_outbox_run_epoch_seq_idx
  ON agent_event_outbox(agent_run_id, epoch, seq);

CREATE TABLE agent_dispatch_outbox (
  outbox_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  manifest_digest bytea NOT NULL,
  attempt integer NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_dispatch_outbox_run_key UNIQUE (agent_run_id),
  CONSTRAINT agent_dispatch_outbox_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_dispatch_outbox_attempt_ck CHECK (attempt >= 0)
);

CREATE TABLE agent_projection_ack (
  agent_run_id uuid NOT NULL,
  consumer text NOT NULL,
  projected_epoch bigint NOT NULL,
  projected_seq bigint NOT NULL,
  producer_close_requested boolean NOT NULL DEFAULT false,
  consumer_closed boolean NOT NULL DEFAULT false,
  generation bigint NOT NULL DEFAULT 1,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_projection_ack_pk PRIMARY KEY (agent_run_id, consumer),
  CONSTRAINT agent_projection_ack_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_projection_ack_consumer_ck CHECK (consumer = 'chat'),
  CONSTRAINT agent_projection_ack_epoch_ck CHECK (projected_epoch > 0),
  CONSTRAINT agent_projection_ack_seq_ck CHECK (projected_seq >= 0),
  CONSTRAINT agent_projection_ack_generation_ck CHECK (generation > 0)
);

CREATE TABLE agent_tool_effect (
  effect_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  tool_call_id text NOT NULL,
  effect_kind text NOT NULL,
  request_digest bytea NOT NULL,
  status text NOT NULL,
  result_digest bytea,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_tool_effect_identity_key
    UNIQUE (agent_run_id, tool_call_id, effect_kind),
  CONSTRAINT agent_tool_effect_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_tool_effect_status_ck
    CHECK (status IN ('claimed','completed','failed','unknown')),
  CONSTRAINT agent_tool_effect_result_ck CHECK (
    (status IN ('claimed','unknown') AND result_digest IS NULL)
    OR (status = 'completed' AND result_digest IS NOT NULL)
    OR status = 'failed'
  )
);

CREATE TABLE agent_run_usage (
  run_usage_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  digest bytea NOT NULL,
  input_tokens bigint NOT NULL,
  output_tokens bigint NOT NULL,
  cached_tokens bigint NOT NULL,
  call_count integer NOT NULL,
  finalized_at timestamptz NOT NULL,
  CONSTRAINT agent_run_usage_run_key UNIQUE (agent_run_id),
  CONSTRAINT agent_run_usage_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_run_usage_nonnegative_ck CHECK (
    input_tokens >= 0 AND output_tokens >= 0 AND cached_tokens >= 0 AND call_count >= 0
  )
);

CREATE TABLE agent_run_usage_line (
  usage_line_id uuid PRIMARY KEY,
  run_usage_id uuid NOT NULL,
  model_revision_id uuid NOT NULL,
  feature_key text NOT NULL,
  input_tokens bigint NOT NULL,
  output_tokens bigint NOT NULL,
  cached_tokens bigint NOT NULL,
  call_count integer NOT NULL,
  CONSTRAINT agent_run_usage_line_identity_key
    UNIQUE (run_usage_id, model_revision_id, feature_key),
  CONSTRAINT agent_run_usage_line_usage_fk
    FOREIGN KEY (run_usage_id) REFERENCES agent_run_usage(run_usage_id) ON DELETE RESTRICT,
  CONSTRAINT agent_run_usage_line_nonnegative_ck CHECK (
    input_tokens >= 0 AND output_tokens >= 0 AND cached_tokens >= 0 AND call_count >= 0
  )
);

CREATE TABLE agent_sandbox_binding (
  binding_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  backend text NOT NULL,
  workspace_ref text NOT NULL,
  state text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_sandbox_binding_run_key UNIQUE (agent_run_id),
  CONSTRAINT agent_sandbox_binding_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_sandbox_binding_state_ck
    CHECK (state IN ('provisioning','ready','released','failed')),
  CONSTRAINT agent_sandbox_binding_generation_ck CHECK (generation > 0)
);

CREATE TABLE agent_memory (
  memory_id uuid PRIMARY KEY,
  namespace text NOT NULL,
  memory_key text NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  expires_at timestamptz,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_memory_namespace_key UNIQUE (namespace, memory_key),
  CONSTRAINT agent_memory_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT agent_memory_payload_ck CHECK (jsonb_typeof(payload) IN ('object','array')),
  CONSTRAINT agent_memory_generation_ck CHECK (generation > 0)
);

CREATE TABLE agent_dispatch_dlq (
  dlq_id uuid PRIMARY KEY,
  agent_run_id uuid,
  request_digest bytea NOT NULL,
  error_code text NOT NULL,
  payload jsonb NOT NULL,
  retry_status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_dispatch_dlq_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_dispatch_dlq_payload_ck CHECK (jsonb_typeof(payload) = 'object'),
  CONSTRAINT agent_dispatch_dlq_retry_status_ck
    CHECK (retry_status IN ('pending','retrying','resolved','abandoned'))
);

CREATE FUNCTION agent_validate_run_manifest_state()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.state IN ('queued','running','awaiting_input','completed','failed','cancelled')
    AND NEW.execution_manifest_id IS NULL
  THEN
    RAISE EXCEPTION 'run state requires an immutable execution manifest'
      USING ERRCODE='23514', CONSTRAINT='agent_run_manifest_required_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_run_manifest_required_trigger
AFTER INSERT OR UPDATE OF state, execution_manifest_id ON agent_run
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_run_manifest_state();

CREATE FUNCTION agent_reject_run_identity_or_terminal_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.launch_id IS DISTINCT FROM OLD.launch_id
    OR NEW.launch_request_digest IS DISTINCT FROM OLD.launch_request_digest
    OR NEW.namespace IS DISTINCT FROM OLD.namespace
    OR (OLD.execution_manifest_id IS NOT NULL
      AND NEW.execution_manifest_id IS DISTINCT FROM OLD.execution_manifest_id)
  THEN
    RAISE EXCEPTION 'agent run identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_run_identity_immutable_ck';
  END IF;
  IF OLD.state IN ('completed','failed','cancelled','admission_failed') AND (
    NEW.state IS DISTINCT FROM OLD.state
    OR NEW.epoch IS DISTINCT FROM OLD.epoch
    OR NEW.next_event_seq IS DISTINCT FROM OLD.next_event_seq
  ) THEN
    RAISE EXCEPTION 'terminal agent run cannot transition or allocate events'
      USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_immutable_ck';
  END IF;
  IF NEW.state IS DISTINCT FROM OLD.state AND NOT (
    (OLD.state = 'preparing' AND NEW.state IN ('queued','admission_failed','cancelled'))
    OR (OLD.state = 'queued' AND NEW.state IN ('running','failed','cancelled'))
    OR (OLD.state = 'running' AND NEW.state IN ('awaiting_input','completed','failed','cancelled'))
    OR (OLD.state = 'awaiting_input' AND NEW.state IN ('running','completed','failed','cancelled'))
  ) THEN
    RAISE EXCEPTION 'invalid agent run state transition: % -> %', OLD.state, NEW.state
      USING ERRCODE='23514', CONSTRAINT='agent_run_state_transition_ck';
  END IF;
  IF NEW.epoch < OLD.epoch OR NEW.epoch > OLD.epoch + 1
    OR NEW.next_event_seq < OLD.next_event_seq
    OR NEW.next_event_seq > OLD.next_event_seq + 1
  THEN
    RAISE EXCEPTION 'agent run cursors must advance one step at a time'
      USING ERRCODE='23514', CONSTRAINT='agent_run_cursor_monotonic_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_run_identity_terminal_trigger
BEFORE UPDATE OF launch_id, launch_request_digest, namespace, execution_manifest_id,
  state, epoch, next_event_seq
ON agent_run
FOR EACH ROW EXECUTE FUNCTION agent_reject_run_identity_or_terminal_update();

CREATE FUNCTION agent_validate_event_cursor_allocation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.next_event_seq IS DISTINCT FROM OLD.next_event_seq AND NOT EXISTS (
    SELECT 1 FROM agent_event_outbox
    WHERE agent_run_id = NEW.agent_run_id
      AND epoch = NEW.epoch
      AND seq = NEW.next_event_seq - 1
  ) THEN
    RAISE EXCEPTION 'event cursor allocation requires its event in the same transaction'
      USING ERRCODE='23514', CONSTRAINT='agent_run_event_allocation_complete_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_run_event_allocation_complete_trigger
AFTER UPDATE OF next_event_seq ON agent_run
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_event_cursor_allocation();

CREATE FUNCTION agent_reject_manifest_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'execution manifest is immutable'
    USING ERRCODE='23514', CONSTRAINT='agent_execution_manifest_immutable_ck';
END;
$$;

CREATE TRIGGER agent_execution_manifest_immutable_trigger
BEFORE UPDATE OR DELETE ON agent_execution_manifest
FOR EACH ROW EXECUTE FUNCTION agent_reject_manifest_update();

CREATE FUNCTION agent_validate_event_epoch()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE current_epoch bigint;
DECLARE current_next_event_seq bigint;
DECLARE current_state text;
BEGIN
  SELECT epoch, next_event_seq, state
  INTO current_epoch, current_next_event_seq, current_state FROM agent_run
  WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
  IF current_epoch IS NULL OR NEW.epoch <> current_epoch THEN
    RAISE EXCEPTION 'event epoch does not match current run epoch'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_current_epoch_ck';
  END IF;
  IF NEW.seq <> current_next_event_seq - 1 THEN
    RAISE EXCEPTION 'event sequence must be the run-global allocated cursor'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_allocated_seq_ck';
  END IF;
  IF current_state IN ('completed','failed','cancelled','admission_failed') THEN
    RAISE EXCEPTION 'terminal agent run cannot append events'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_terminal_run_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_event_outbox_current_epoch_trigger
BEFORE INSERT ON agent_event_outbox
FOR EACH ROW EXECUTE FUNCTION agent_validate_event_epoch();

CREATE FUNCTION agent_validate_event_evidence_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE safe_watermark bigint;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.published_at IS NOT NULL OR NEW.acked_at IS NOT NULL THEN
      RAISE EXCEPTION 'event must start unpublished and unacknowledged'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_initial_state_ck';
    END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN
    IF OLD.published_at IS NULL OR OLD.acked_at IS NULL THEN
      RAISE EXCEPTION 'unpublished or unacknowledged event cannot be retained away'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_retention_state_ck';
    END IF;
    SELECT projected_seq INTO safe_watermark
    FROM agent_projection_ack
    WHERE agent_run_id = OLD.agent_run_id AND consumer = 'chat'
    FOR SHARE;
    IF safe_watermark IS NULL OR safe_watermark < OLD.seq THEN
      RAISE EXCEPTION 'event is above the Chat projection safe watermark'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_retention_watermark_ck';
    END IF;
    RETURN OLD;
  END IF;
  IF NEW.event_id IS DISTINCT FROM OLD.event_id
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.epoch IS DISTINCT FROM OLD.epoch
    OR NEW.seq IS DISTINCT FROM OLD.seq
    OR NEW.kind IS DISTINCT FROM OLD.kind
    OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
    OR NEW.payload IS DISTINCT FROM OLD.payload
    OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION 'committed event identity and payload are immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_evidence_immutable_ck';
  END IF;
  IF OLD.published_at IS NOT NULL
    AND NEW.published_at IS DISTINCT FROM OLD.published_at
  THEN
    RAISE EXCEPTION 'event publication timestamp cannot be cleared or rewritten'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_published_once_ck';
  END IF;
  IF OLD.acked_at IS NOT NULL AND NEW.acked_at IS DISTINCT FROM OLD.acked_at THEN
    RAISE EXCEPTION 'event acknowledgement timestamp cannot be cleared or rewritten'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_acked_once_ck';
  END IF;
  IF NEW.acked_at IS NOT NULL AND NEW.published_at IS NULL THEN
    RAISE EXCEPTION 'event must be published before it is acknowledged'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_publish_before_ack_ck';
  END IF;
  IF NEW.published_at IS NOT NULL AND NEW.published_at < NEW.created_at THEN
    RAISE EXCEPTION 'event publication timestamp precedes creation'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_published_time_ck';
  END IF;
  IF NEW.acked_at IS NOT NULL AND NEW.acked_at < NEW.published_at THEN
    RAISE EXCEPTION 'event acknowledgement timestamp precedes publication'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_acked_time_ck';
  END IF;
  IF OLD.acked_at IS NULL AND NEW.acked_at IS NOT NULL THEN
    SELECT projected_seq INTO safe_watermark
    FROM agent_projection_ack
    WHERE agent_run_id = NEW.agent_run_id AND consumer = 'chat'
    FOR SHARE;
    IF safe_watermark IS NULL OR safe_watermark < NEW.seq THEN
      RAISE EXCEPTION 'event acknowledgement requires the Chat projection watermark'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_ack_watermark_ck';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_event_outbox_evidence_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_event_outbox
FOR EACH ROW EXECUTE FUNCTION agent_validate_event_evidence_mutation();

CREATE FUNCTION agent_reject_projection_ack_regression()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE current_epoch bigint;
DECLARE current_next_event_seq bigint;
BEGIN
  SELECT epoch, next_event_seq
  INTO current_epoch, current_next_event_seq
  FROM agent_run
  WHERE agent_run_id = NEW.agent_run_id
  FOR SHARE;
  IF current_epoch IS NULL
    OR NEW.projected_epoch <> current_epoch
    OR NEW.projected_seq > current_next_event_seq - 1
  THEN
    RAISE EXCEPTION 'projection acknowledgement is outside the current run fence'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_current_fence_ck';
  END IF;
  IF NEW.projected_seq > 0
    AND (TG_OP = 'INSERT'
      OR NEW.projected_epoch IS DISTINCT FROM OLD.projected_epoch
      OR NEW.projected_seq > OLD.projected_seq)
    AND NOT EXISTS (
    SELECT 1 FROM agent_event_outbox
    WHERE agent_run_id = NEW.agent_run_id
      AND epoch = NEW.projected_epoch
      AND seq = NEW.projected_seq
      AND published_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'projection acknowledgement requires a published existing event'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_published_event_ck';
  END IF;
  IF TG_OP = 'UPDATE' AND (
    NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.consumer IS DISTINCT FROM OLD.consumer
    OR NEW.projected_epoch < OLD.projected_epoch
    OR NEW.projected_seq < OLD.projected_seq
  ) THEN
    RAISE EXCEPTION 'projection acknowledgement cannot regress or change identity'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_monotonic_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_projection_ack_monotonic_trigger
BEFORE INSERT OR UPDATE ON agent_projection_ack
FOR EACH ROW EXECUTE FUNCTION agent_reject_projection_ack_regression();

CREATE FUNCTION agent_validate_tool_effect_transition()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE run_state text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'tool effect evidence cannot be deleted'
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_immutable_ck';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'claimed' OR NEW.result_digest IS NOT NULL THEN
      RAISE EXCEPTION 'tool effect must be claimed before an external effect'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_claim_first_ck';
    END IF;
    SELECT state INTO run_state
    FROM agent_run
    WHERE agent_run_id = NEW.agent_run_id
    FOR SHARE;
    IF run_state IN ('completed','failed','cancelled','admission_failed') THEN
      RAISE EXCEPTION 'terminal agent run cannot claim a new tool effect'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_terminal_run_ck';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.effect_id IS DISTINCT FROM OLD.effect_id
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.tool_call_id IS DISTINCT FROM OLD.tool_call_id
    OR NEW.effect_kind IS DISTINCT FROM OLD.effect_kind
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
    OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION 'tool effect claim identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_claim_immutable_ck';
  END IF;
  IF OLD.status IN ('completed','failed') AND (
    NEW.status IS DISTINCT FROM OLD.status
    OR NEW.result_digest IS DISTINCT FROM OLD.result_digest
  ) THEN
    RAISE EXCEPTION 'terminal tool effect result is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_terminal_immutable_ck';
  END IF;
  IF NEW.status IS DISTINCT FROM OLD.status AND NOT (
    (OLD.status = 'claimed' AND NEW.status IN ('completed','failed','unknown'))
    OR (OLD.status = 'unknown' AND NEW.status IN ('completed','failed'))
  ) THEN
    RAISE EXCEPTION 'invalid tool effect transition: % -> %', OLD.status, NEW.status
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_transition_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_tool_effect_transition_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_tool_effect
FOR EACH ROW EXECUTE FUNCTION agent_validate_tool_effect_transition();

CREATE FUNCTION agent_validate_terminal_run_usage()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE run_state text;
BEGIN
  SELECT state INTO run_state
  FROM agent_run
  WHERE agent_run_id = NEW.agent_run_id
  FOR SHARE;
  IF run_state NOT IN ('completed','failed','cancelled','admission_failed') THEN
    RAISE EXCEPTION 'run usage can only be finalized for a terminal run'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_terminal_run_ck';
  END IF;
  IF NEW.finalized_at IS DISTINCT FROM transaction_timestamp() THEN
    RAISE EXCEPTION 'run usage must be finalized in its creation transaction'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_finalization_time_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_run_usage_terminal_trigger
AFTER INSERT ON agent_run_usage
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_terminal_run_usage();

CREATE FUNCTION agent_reject_run_usage_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'finalized run usage is immutable'
    USING ERRCODE='23514', CONSTRAINT='agent_run_usage_immutable_ck';
END;
$$;

CREATE TRIGGER agent_run_usage_immutable_trigger
BEFORE UPDATE OR DELETE ON agent_run_usage
FOR EACH ROW EXECUTE FUNCTION agent_reject_run_usage_mutation();

CREATE FUNCTION agent_validate_run_usage_line_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE usage_finalized_at timestamptz;
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION 'run usage lines are append-only finalization evidence'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_line_immutable_ck';
  END IF;
  SELECT finalized_at INTO usage_finalized_at
  FROM agent_run_usage
  WHERE run_usage_id = NEW.run_usage_id
  FOR SHARE;
  IF usage_finalized_at IS DISTINCT FROM transaction_timestamp() THEN
    RAISE EXCEPTION 'run usage lines must be inserted with their aggregate'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_line_same_transaction_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_run_usage_line_immutable_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_run_usage_line
FOR EACH ROW EXECUTE FUNCTION agent_validate_run_usage_line_mutation();

CREATE FUNCTION agent_reject_control_claim_update()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE run_state text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'agent control receipt cannot be deleted'
      USING ERRCODE='23514', CONSTRAINT='agent_control_inbox_immutable_ck';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'pending' OR NEW.applied_at IS NOT NULL THEN
      RAISE EXCEPTION 'agent control receipt must start pending'
        USING ERRCODE='23514', CONSTRAINT='agent_control_inbox_claim_first_ck';
    END IF;
    SELECT state INTO run_state
    FROM agent_run
    WHERE agent_run_id = NEW.agent_run_id
    FOR SHARE;
    IF run_state IN ('completed','failed','cancelled','admission_failed') THEN
      RAISE EXCEPTION 'terminal agent run cannot claim a new control command'
        USING ERRCODE='23514', CONSTRAINT='agent_control_inbox_terminal_run_ck';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.control_id IS DISTINCT FROM OLD.control_id
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.command_id IS DISTINCT FROM OLD.command_id
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
    OR NEW.command_schema_version IS DISTINCT FROM OLD.command_schema_version
    OR NEW.command_payload IS DISTINCT FROM OLD.command_payload
    OR NEW.interrupt_fingerprint IS DISTINCT FROM OLD.interrupt_fingerprint
    OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION 'agent control claim is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_control_inbox_claim_immutable_ck';
  END IF;
  IF OLD.status IN ('applied','rejected','failed') AND (
    NEW.status IS DISTINCT FROM OLD.status
    OR NEW.applied_at IS DISTINCT FROM OLD.applied_at
  ) THEN
    RAISE EXCEPTION 'terminal agent control receipt is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_control_inbox_terminal_immutable_ck';
  END IF;
  IF NEW.status IS DISTINCT FROM OLD.status AND NOT (
    OLD.status = 'pending' AND NEW.status IN ('applied','rejected','failed')
  ) THEN
    RAISE EXCEPTION 'invalid agent control transition: % -> %', OLD.status, NEW.status
      USING ERRCODE='23514', CONSTRAINT='agent_control_inbox_transition_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_control_inbox_claim_immutable_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_control_inbox
FOR EACH ROW EXECUTE FUNCTION agent_reject_control_claim_update();
