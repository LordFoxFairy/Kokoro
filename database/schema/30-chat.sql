SET search_path TO kokoro, pg_catalog;

CREATE TABLE chat_conversation (
  conversation_id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  site_id uuid NOT NULL,
  created_by_principal_id uuid NOT NULL,
  title text NOT NULL,
  agent_namespace text NOT NULL,
  state text NOT NULL,
  next_stream_seq bigint NOT NULL DEFAULT 1,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_conversation_organization_site_fk
    FOREIGN KEY (organization_id, site_id)
    REFERENCES iam_organization(organization_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT chat_conversation_principal_site_fk
    FOREIGN KEY (created_by_principal_id, site_id)
    REFERENCES iam_principal(principal_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT chat_conversation_conversation_organization_key
    UNIQUE (conversation_id, organization_id),
  CONSTRAINT chat_conversation_conversation_site_key
    UNIQUE (conversation_id, site_id),
  CONSTRAINT chat_conversation_agent_namespace_key UNIQUE (agent_namespace),
  CONSTRAINT chat_conversation_state_ck CHECK (state IN ('active','archived','trashed')),
  CONSTRAINT chat_conversation_next_stream_seq_ck CHECK (next_stream_seq > 0),
  CONSTRAINT chat_conversation_generation_ck CHECK (generation > 0)
);

CREATE TABLE chat_message (
  message_id uuid PRIMARY KEY,
  conversation_id uuid NOT NULL,
  parent_message_id uuid,
  role text NOT NULL,
  status text NOT NULL,
  ordinal bigint NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_message_conversation_fk
    FOREIGN KEY (conversation_id) REFERENCES chat_conversation(conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_message_message_conversation_key UNIQUE (message_id, conversation_id),
  CONSTRAINT chat_message_parent_conversation_fk
    FOREIGN KEY (parent_message_id, conversation_id)
    REFERENCES chat_message(message_id, conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_message_conversation_ordinal_key UNIQUE (conversation_id, ordinal),
  CONSTRAINT chat_message_role_ck CHECK (role IN ('user','assistant','system','tool')),
  CONSTRAINT chat_message_status_ck CHECK (status IN ('pending','streaming','complete','failed')),
  CONSTRAINT chat_message_ordinal_ck CHECK (ordinal > 0),
  CONSTRAINT chat_message_generation_ck CHECK (generation > 0)
);

CREATE TABLE chat_message_part (
  part_id uuid PRIMARY KEY,
  message_id uuid NOT NULL,
  ordinal bigint NOT NULL,
  kind text NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_message_part_message_fk
    FOREIGN KEY (message_id) REFERENCES chat_message(message_id) ON DELETE RESTRICT,
  CONSTRAINT chat_message_part_message_ordinal_key UNIQUE (message_id, ordinal),
  CONSTRAINT chat_message_part_ordinal_ck CHECK (ordinal > 0),
  CONSTRAINT chat_message_part_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT chat_message_part_payload_ck CHECK (jsonb_typeof(payload) IN ('object','array')),
  CONSTRAINT chat_message_part_status_ck CHECK (status IN ('pending','streaming','complete','failed')),
  CONSTRAINT chat_message_part_generation_ck CHECK (generation > 0)
);

CREATE TABLE chat_command_receipt (
  receipt_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  organization_id uuid NOT NULL,
  conversation_id uuid,
  command_id uuid NOT NULL,
  command_kind text NOT NULL,
  request_digest bytea NOT NULL,
  status text NOT NULL,
  result_ref text,
  result_payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_command_receipt_organization_site_fk
    FOREIGN KEY (organization_id, site_id)
    REFERENCES iam_organization(organization_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT chat_command_receipt_conversation_organization_fk
    FOREIGN KEY (conversation_id, organization_id)
    REFERENCES chat_conversation(conversation_id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT chat_command_receipt_receipt_scope_key
    UNIQUE (receipt_id, conversation_id, organization_id),
  CONSTRAINT chat_command_receipt_organization_command_key
    UNIQUE (organization_id, command_id),
  CONSTRAINT chat_command_receipt_status_ck CHECK (status IN ('processing','completed','failed')),
  CONSTRAINT chat_command_receipt_result_payload_ck CHECK (
    result_payload IS NULL OR jsonb_typeof(result_payload) IN ('object','array')
  )
);

CREATE TABLE chat_run_launch (
  launch_id uuid PRIMARY KEY,
  conversation_id uuid NOT NULL,
  user_message_id uuid NOT NULL,
  assistant_message_id uuid NOT NULL,
  requested_model_ref text,
  requested_agent_ref text,
  state text NOT NULL,
  agent_run_id uuid,
  manifest_digest bytea,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_run_launch_conversation_fk
    FOREIGN KEY (conversation_id) REFERENCES chat_conversation(conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_run_launch_user_message_conversation_fk
    FOREIGN KEY (user_message_id, conversation_id)
    REFERENCES chat_message(message_id, conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_run_launch_assistant_message_conversation_fk
    FOREIGN KEY (assistant_message_id, conversation_id)
    REFERENCES chat_message(message_id, conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_run_launch_launch_conversation_key UNIQUE (launch_id, conversation_id),
  CONSTRAINT chat_run_launch_messages_distinct_ck CHECK (
    assistant_message_id IS NULL OR assistant_message_id <> user_message_id
  ),
  CONSTRAINT chat_run_launch_state_ck CHECK (state IN ('submitted','accepted','rejected','completed')),
  CONSTRAINT chat_run_launch_generation_ck CHECK (generation > 0)
);

CREATE TABLE chat_active_run (
  conversation_id uuid NOT NULL,
  launch_id uuid NOT NULL,
  acquired_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_active_run_pk PRIMARY KEY (conversation_id),
  CONSTRAINT chat_active_run_launch_key UNIQUE (launch_id),
  CONSTRAINT chat_active_run_launch_conversation_fk
    FOREIGN KEY (launch_id, conversation_id)
    REFERENCES chat_run_launch(launch_id, conversation_id) ON DELETE RESTRICT
);

CREATE TABLE chat_run_view (
  agent_run_id uuid PRIMARY KEY,
  launch_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  epoch bigint NOT NULL,
  state text NOT NULL,
  received_seq bigint NOT NULL DEFAULT 0,
  projected_seq bigint NOT NULL DEFAULT 0,
  terminal_kind text,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_run_view_agent_run_conversation_key UNIQUE (agent_run_id, conversation_id),
  CONSTRAINT chat_run_view_launch_key UNIQUE (launch_id),
  CONSTRAINT chat_run_view_launch_conversation_fk
    FOREIGN KEY (launch_id, conversation_id)
    REFERENCES chat_run_launch(launch_id, conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_run_view_epoch_ck CHECK (epoch > 0),
  CONSTRAINT chat_run_view_sequences_ck CHECK (received_seq >= 0 AND projected_seq >= 0 AND projected_seq <= received_seq),
  CONSTRAINT chat_run_view_state_ck CHECK (state IN ('queued','running','paused','completed','failed','cancelled')),
  CONSTRAINT chat_run_view_terminal_ck CHECK (
    (state IN ('completed','failed','cancelled') AND terminal_kind IS NOT NULL)
    OR (state NOT IN ('completed','failed','cancelled') AND terminal_kind IS NULL)
  ),
  CONSTRAINT chat_run_view_generation_ck CHECK (generation > 0)
);

CREATE TABLE chat_interaction (
  interaction_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  kind text NOT NULL,
  action_digest bytea NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL,
  expires_at timestamptz,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_interaction_run_conversation_fk
    FOREIGN KEY (agent_run_id, conversation_id)
    REFERENCES chat_run_view(agent_run_id, conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_interaction_interaction_conversation_key UNIQUE (interaction_id, conversation_id),
  CONSTRAINT chat_interaction_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT chat_interaction_payload_ck CHECK (jsonb_typeof(payload) IN ('object','array')),
  CONSTRAINT chat_interaction_status_ck CHECK (status IN ('pending','resolved','cancelled','expired')),
  CONSTRAINT chat_interaction_generation_ck CHECK (generation > 0)
);

CREATE TABLE chat_control_command (
  control_id uuid PRIMARY KEY,
  receipt_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  organization_id uuid NOT NULL,
  interaction_id uuid,
  expected_generation bigint NOT NULL,
  decisions jsonb NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_control_command_receipt_key UNIQUE (receipt_id),
  CONSTRAINT chat_control_command_receipt_scope_fk
    FOREIGN KEY (receipt_id, conversation_id, organization_id)
    REFERENCES chat_command_receipt(receipt_id, conversation_id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT chat_control_command_interaction_conversation_fk
    FOREIGN KEY (interaction_id, conversation_id)
    REFERENCES chat_interaction(interaction_id, conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_control_command_generation_ck CHECK (expected_generation > 0),
  CONSTRAINT chat_control_command_decisions_ck CHECK (
    jsonb_typeof(decisions) = 'array' AND jsonb_array_length(decisions) > 0
  ),
  CONSTRAINT chat_control_command_status_ck CHECK (status IN ('pending','published','applied','failed'))
);

CREATE TABLE chat_control_outbox (
  outbox_id uuid PRIMARY KEY,
  control_id uuid NOT NULL,
  payload jsonb NOT NULL,
  attempt integer NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  acked_at timestamptz,
  CONSTRAINT chat_control_outbox_control_key UNIQUE (control_id),
  CONSTRAINT chat_control_outbox_control_fk
    FOREIGN KEY (control_id) REFERENCES chat_control_command(control_id) ON DELETE RESTRICT,
  CONSTRAINT chat_control_outbox_payload_ck CHECK (jsonb_typeof(payload) = 'object'),
  CONSTRAINT chat_control_outbox_attempt_ck CHECK (attempt >= 0)
);

CREATE TABLE chat_launch_outbox (
  outbox_id uuid PRIMARY KEY,
  launch_id uuid NOT NULL,
  request_digest bytea NOT NULL,
  payload jsonb NOT NULL,
  attempt integer NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  accepted_at timestamptz,
  CONSTRAINT chat_launch_outbox_launch_key UNIQUE (launch_id),
  CONSTRAINT chat_launch_outbox_launch_fk
    FOREIGN KEY (launch_id) REFERENCES chat_run_launch(launch_id) ON DELETE RESTRICT,
  CONSTRAINT chat_launch_outbox_payload_ck CHECK (jsonb_typeof(payload) = 'object'),
  CONSTRAINT chat_launch_outbox_attempt_ck CHECK (attempt >= 0)
);

CREATE TABLE chat_projection_inbox (
  inbox_id uuid PRIMARY KEY,
  producer text NOT NULL,
  agent_run_id uuid NOT NULL,
  epoch bigint NOT NULL,
  producer_seq bigint NOT NULL,
  event_id uuid NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_projection_inbox_event_key UNIQUE (event_id),
  CONSTRAINT chat_projection_inbox_producer_run_seq_key UNIQUE (producer, agent_run_id, producer_seq),
  CONSTRAINT chat_projection_inbox_epoch_ck CHECK (epoch > 0),
  CONSTRAINT chat_projection_inbox_producer_seq_ck CHECK (producer_seq > 0),
  CONSTRAINT chat_projection_inbox_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT chat_projection_inbox_payload_ck CHECK (jsonb_typeof(payload) IN ('object','array')),
  CONSTRAINT chat_projection_inbox_status_ck CHECK (status IN ('pending','projected','failed'))
);

CREATE TABLE chat_projection_dlq (
  dlq_id uuid PRIMARY KEY,
  inbox_id uuid NOT NULL,
  error_code text NOT NULL,
  repair_status text NOT NULL,
  attempt integer NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_projection_dlq_inbox_key UNIQUE (inbox_id),
  CONSTRAINT chat_projection_dlq_inbox_fk
    FOREIGN KEY (inbox_id) REFERENCES chat_projection_inbox(inbox_id) ON DELETE RESTRICT,
  CONSTRAINT chat_projection_dlq_repair_status_ck CHECK (repair_status IN ('pending','replaying','resolved','abandoned')),
  CONSTRAINT chat_projection_dlq_attempt_ck CHECK (attempt >= 0)
);

CREATE TABLE chat_stream_event (
  stream_event_id uuid PRIMARY KEY,
  conversation_id uuid NOT NULL,
  seq bigint NOT NULL,
  event_id uuid NOT NULL,
  kind text NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chat_stream_event_conversation_fk
    FOREIGN KEY (conversation_id) REFERENCES chat_conversation(conversation_id) ON DELETE RESTRICT,
  CONSTRAINT chat_stream_event_conversation_seq_key UNIQUE (conversation_id, seq),
  CONSTRAINT chat_stream_event_conversation_event_key UNIQUE (conversation_id, event_id),
  CONSTRAINT chat_stream_event_seq_ck CHECK (seq > 0),
  CONSTRAINT chat_stream_event_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT chat_stream_event_payload_ck CHECK (jsonb_typeof(payload) IN ('object','array'))
);

CREATE FUNCTION chat_reject_command_receipt_claim_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.site_id IS DISTINCT FROM OLD.site_id
    OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
    OR NEW.conversation_id IS DISTINCT FROM OLD.conversation_id
    OR NEW.command_id IS DISTINCT FROM OLD.command_id
    OR NEW.command_kind IS DISTINCT FROM OLD.command_kind
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
  THEN
    RAISE EXCEPTION 'chat command receipt claim is immutable'
      USING ERRCODE='23514', CONSTRAINT='chat_command_receipt_claim_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_command_receipt_claim_immutable_trigger
BEFORE UPDATE OF site_id, organization_id, conversation_id, command_id, command_kind, request_digest
ON chat_command_receipt
FOR EACH ROW EXECUTE FUNCTION chat_reject_command_receipt_claim_update();

CREATE FUNCTION chat_reject_conversation_identity_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.organization_id IS DISTINCT FROM OLD.organization_id
    OR NEW.site_id IS DISTINCT FROM OLD.site_id
    OR NEW.created_by_principal_id IS DISTINCT FROM OLD.created_by_principal_id
    OR NEW.agent_namespace IS DISTINCT FROM OLD.agent_namespace
  THEN
    RAISE EXCEPTION 'conversation tenant identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='chat_conversation_identity_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_conversation_identity_immutable_trigger
BEFORE UPDATE OF organization_id, site_id, created_by_principal_id, agent_namespace
ON chat_conversation
FOR EACH ROW EXECUTE FUNCTION chat_reject_conversation_identity_update();

CREATE FUNCTION chat_reject_message_identity_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.conversation_id IS DISTINCT FROM OLD.conversation_id
    OR NEW.parent_message_id IS DISTINCT FROM OLD.parent_message_id
    OR NEW.role IS DISTINCT FROM OLD.role
    OR NEW.ordinal IS DISTINCT FROM OLD.ordinal
  THEN
    RAISE EXCEPTION 'message owner identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='chat_message_identity_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_message_identity_immutable_trigger
BEFORE UPDATE OF conversation_id, parent_message_id, role, ordinal
ON chat_message
FOR EACH ROW EXECUTE FUNCTION chat_reject_message_identity_update();

CREATE FUNCTION chat_reject_stream_seq_regression()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.next_stream_seq < OLD.next_stream_seq THEN
    RAISE EXCEPTION 'conversation stream sequence cannot regress'
      USING ERRCODE='23514', CONSTRAINT='chat_conversation_stream_seq_monotonic_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_conversation_stream_seq_monotonic_trigger
BEFORE UPDATE OF next_stream_seq ON chat_conversation
FOR EACH ROW EXECUTE FUNCTION chat_reject_stream_seq_regression();

CREATE FUNCTION chat_reject_accepted_launch_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF (
    (OLD.state = 'accepted' AND NEW.state NOT IN ('accepted','completed'))
    OR (OLD.state IN ('completed','rejected') AND NEW.state <> OLD.state)
  ) OR (OLD.state IN ('accepted','completed','rejected') AND (
    NEW.conversation_id IS DISTINCT FROM OLD.conversation_id
    OR NEW.user_message_id IS DISTINCT FROM OLD.user_message_id
    OR NEW.assistant_message_id IS DISTINCT FROM OLD.assistant_message_id
    OR NEW.requested_model_ref IS DISTINCT FROM OLD.requested_model_ref
    OR NEW.requested_agent_ref IS DISTINCT FROM OLD.requested_agent_ref
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.manifest_digest IS DISTINCT FROM OLD.manifest_digest
  )) THEN
    RAISE EXCEPTION 'accepted launch identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='chat_run_launch_accepted_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_run_launch_accepted_immutable_trigger
BEFORE UPDATE OF state, conversation_id, user_message_id, assistant_message_id,
  requested_model_ref, requested_agent_ref, agent_run_id, manifest_digest
ON chat_run_launch
FOR EACH ROW EXECUTE FUNCTION chat_reject_accepted_launch_update();

CREATE FUNCTION chat_reject_projection_claim_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.producer IS DISTINCT FROM OLD.producer
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.epoch IS DISTINCT FROM OLD.epoch
    OR NEW.producer_seq IS DISTINCT FROM OLD.producer_seq
    OR NEW.event_id IS DISTINCT FROM OLD.event_id
    OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
    OR NEW.payload IS DISTINCT FROM OLD.payload
  THEN
    RAISE EXCEPTION 'projection inbox event claim is immutable'
      USING ERRCODE='23514', CONSTRAINT='chat_projection_inbox_claim_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_projection_inbox_claim_immutable_trigger
BEFORE UPDATE OF producer, agent_run_id, epoch, producer_seq, event_id,
  schema_version, payload
ON chat_projection_inbox
FOR EACH ROW EXECUTE FUNCTION chat_reject_projection_claim_update();

CREATE FUNCTION chat_reject_interaction_payload_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.conversation_id IS DISTINCT FROM OLD.conversation_id
    OR NEW.kind IS DISTINCT FROM OLD.kind
    OR NEW.action_digest IS DISTINCT FROM OLD.action_digest
    OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
    OR NEW.payload IS DISTINCT FROM OLD.payload
  THEN
    RAISE EXCEPTION 'interaction payload identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='chat_interaction_payload_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_interaction_payload_immutable_trigger
BEFORE UPDATE OF agent_run_id, conversation_id, kind, action_digest, schema_version, payload
ON chat_interaction
FOR EACH ROW EXECUTE FUNCTION chat_reject_interaction_payload_update();

CREATE FUNCTION chat_reject_interaction_resurrection()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF OLD.status IN ('resolved','cancelled','expired')
    AND NEW.status IS DISTINCT FROM OLD.status
  THEN
    RAISE EXCEPTION 'terminal interaction cannot transition'
      USING ERRCODE='23514', CONSTRAINT='chat_interaction_terminal_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER chat_interaction_terminal_immutable_trigger
BEFORE UPDATE OF status ON chat_interaction
FOR EACH ROW EXECUTE FUNCTION chat_reject_interaction_resurrection();

CREATE FUNCTION chat_check_control_interaction_requirement()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE
  receipt_kind text;
BEGIN
  SELECT command_kind INTO receipt_kind
  FROM chat_command_receipt
  WHERE receipt_id = NEW.receipt_id
    AND conversation_id = NEW.conversation_id
    AND organization_id = NEW.organization_id;
  IF receipt_kind = 'DecideInteraction' AND NEW.interaction_id IS NULL THEN
    RAISE EXCEPTION 'DecideInteraction control requires an interaction'
      USING ERRCODE='23514', CONSTRAINT='chat_control_command_decide_interaction_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER chat_control_command_decide_interaction_trigger
AFTER INSERT OR UPDATE OF receipt_id, conversation_id, organization_id, interaction_id
ON chat_control_command
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION chat_check_control_interaction_requirement();
