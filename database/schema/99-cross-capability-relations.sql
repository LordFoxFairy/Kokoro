SET search_path TO kokoro, pg_catalog;

ALTER TABLE agent_execution_manifest
  ADD CONSTRAINT agent_execution_manifest_model_revision_fk
  FOREIGN KEY (model_revision_id)
  REFERENCES model_revision(model_revision_id) ON DELETE RESTRICT,
  ADD CONSTRAINT agent_execution_manifest_capability_snapshot_namespace_fk
  FOREIGN KEY (capability_snapshot_id, namespace)
  REFERENCES capability_runtime_snapshot(snapshot_id, scope_key) ON DELETE RESTRICT;

ALTER TABLE agent_run_usage_line
  ADD CONSTRAINT agent_run_usage_line_model_revision_fk
  FOREIGN KEY (model_revision_id)
  REFERENCES model_revision(model_revision_id) ON DELETE RESTRICT;

CREATE FUNCTION agent_validate_manifest_targets()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target_published_at timestamptz;
DECLARE target_transport text;
BEGIN
  SELECT published_at, transport
  INTO target_published_at, target_transport
  FROM model_revision
  WHERE model_revision_id = NEW.model_revision_id;
  IF target_published_at IS NULL OR target_transport <> 'litellm' THEN
    RAISE EXCEPTION 'execution manifest requires a published LiteLLM model revision'
      USING ERRCODE='23514', CONSTRAINT='agent_execution_manifest_published_model_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_execution_manifest_target_trigger
AFTER INSERT ON agent_execution_manifest
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_manifest_targets();
