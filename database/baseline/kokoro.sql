-- source: database/schema/00-foundation.sql
-- sha256: fef216ee782ba041970425a2866862be6b4aabe450d0db00cba0fd3c563dfade
CREATE SCHEMA IF NOT EXISTS kokoro;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA kokoro;
ALTER ROLE CURRENT_USER SET search_path TO kokoro, pg_catalog;
SET search_path TO kokoro, pg_catalog;

-- source: database/schema/10-site.sql
-- sha256: ff6dcd674fdc9cfc1a39ba44ef09cb86c99ccb028e70cca7536afd2eb6605d4e
SET search_path TO kokoro, pg_catalog;

CREATE TABLE site_site (
  site_id uuid PRIMARY KEY,
  key text NOT NULL,
  name text NOT NULL,
  status text NOT NULL,
  default_locale text NOT NULL,
  timezone text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT site_site_key_key UNIQUE (key),
  CONSTRAINT site_site_status_ck CHECK (status IN ('draft', 'active', 'suspended')),
  CONSTRAINT site_site_generation_ck CHECK (generation > 0)
);

CREATE TABLE site_domain (
  domain_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  normalized_host text NOT NULL,
  status text NOT NULL,
  is_primary boolean NOT NULL DEFAULT false,
  verification_token_hash bytea,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT site_domain_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT site_domain_normalized_host_key UNIQUE (normalized_host),
  CONSTRAINT site_domain_status_ck CHECK (status IN ('pending', 'active', 'disabled')),
  CONSTRAINT site_domain_verified_ck CHECK (
    status <> 'active' OR verified_at IS NOT NULL
  )
);

CREATE UNIQUE INDEX site_domain_one_active_primary_uidx
  ON site_domain(site_id)
  WHERE is_primary AND status = 'active';

-- source: database/schema/20-iam.sql
-- sha256: a1cfd6ebbd71c49581a3a6a3f74f010f200ee1a162240fc6e374ea5a6d8f1fda
SET search_path TO kokoro, pg_catalog;

CREATE TABLE iam_principal (
  principal_id uuid PRIMARY KEY,
  principal_scope text NOT NULL,
  site_id uuid,
  kind text NOT NULL,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_principal_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_principal_principal_site_key UNIQUE (principal_id, site_id),
  CONSTRAINT iam_principal_scope_kind_ck CHECK (
    (
      principal_scope = 'site'
      AND site_id IS NOT NULL
      AND kind IN ('user', 'service_account')
    ) OR (
      principal_scope = 'control_plane'
      AND site_id IS NULL
      AND kind = 'operator'
    )
  ),
  CONSTRAINT iam_principal_status_ck CHECK (status IN ('active', 'disabled', 'deleted')),
  CONSTRAINT iam_principal_generation_ck CHECK (generation > 0)
);

CREATE TABLE iam_user (
  principal_id uuid PRIMARY KEY,
  display_name text NOT NULL,
  avatar_url text,
  locale text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_user_principal_fk
    FOREIGN KEY (principal_id) REFERENCES iam_principal(principal_id) ON DELETE RESTRICT
);

CREATE TABLE iam_identity (
  identity_id uuid PRIMARY KEY,
  principal_scope text NOT NULL,
  site_id uuid,
  principal_id uuid NOT NULL,
  issuer text NOT NULL,
  subject text NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_identity_principal_fk
    FOREIGN KEY (principal_id) REFERENCES iam_principal(principal_id) ON DELETE RESTRICT,
  CONSTRAINT iam_identity_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_identity_scope_ck CHECK (
    (principal_scope = 'site' AND site_id IS NOT NULL)
    OR (principal_scope = 'control_plane' AND site_id IS NULL)
  ),
  CONSTRAINT iam_identity_status_ck CHECK (status IN ('active', 'revoked'))
);

CREATE UNIQUE INDEX iam_identity_site_subject_uidx
  ON iam_identity(site_id, issuer, subject)
  WHERE principal_scope = 'site';

CREATE UNIQUE INDEX iam_identity_control_plane_subject_uidx
  ON iam_identity(issuer, subject)
  WHERE principal_scope = 'control_plane';

CREATE TABLE iam_contact (
  contact_id uuid PRIMARY KEY,
  principal_scope text NOT NULL,
  site_id uuid,
  principal_id uuid NOT NULL,
  kind text NOT NULL,
  normalized_value text NOT NULL,
  status text NOT NULL,
  verified_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_contact_principal_fk
    FOREIGN KEY (principal_id) REFERENCES iam_principal(principal_id) ON DELETE RESTRICT,
  CONSTRAINT iam_contact_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_contact_scope_ck CHECK (
    (principal_scope = 'site' AND site_id IS NOT NULL)
    OR (principal_scope = 'control_plane' AND site_id IS NULL)
  ),
  CONSTRAINT iam_contact_kind_ck CHECK (kind IN ('email', 'phone')),
  CONSTRAINT iam_contact_status_ck CHECK (status IN ('active', 'revoked')),
  CONSTRAINT iam_contact_revoked_at_ck CHECK (
    (status = 'active' AND revoked_at IS NULL)
    OR (status = 'revoked' AND revoked_at IS NOT NULL)
  )
);

CREATE UNIQUE INDEX iam_contact_site_active_value_uidx
  ON iam_contact(site_id, kind, normalized_value)
  WHERE principal_scope = 'site' AND status = 'active';

CREATE UNIQUE INDEX iam_contact_control_plane_active_value_uidx
  ON iam_contact(kind, normalized_value)
  WHERE principal_scope = 'control_plane' AND status = 'active';

CREATE TABLE iam_magic_link (
  magic_link_id uuid PRIMARY KEY,
  principal_scope text NOT NULL,
  site_id uuid,
  normalized_email text NOT NULL,
  token_hash bytea NOT NULL,
  nonce_hash bytea,
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  superseded_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_magic_link_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_magic_link_token_hash_key UNIQUE (token_hash),
  CONSTRAINT iam_magic_link_scope_ck CHECK (
    (principal_scope = 'site' AND site_id IS NOT NULL)
    OR (principal_scope = 'control_plane' AND site_id IS NULL)
  ),
  CONSTRAINT iam_magic_link_terminal_ck CHECK (
    consumed_at IS NULL OR superseded_at IS NULL
  ),
  CONSTRAINT iam_magic_link_expiry_ck CHECK (expires_at > created_at)
);

CREATE TABLE iam_command_receipt (
  receipt_id uuid PRIMARY KEY,
  command_id uuid NOT NULL,
  command_kind text NOT NULL,
  request_digest bytea NOT NULL,
  status text NOT NULL,
  result_ref text,
  result_payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_command_receipt_command_id_key UNIQUE (command_id),
  CONSTRAINT iam_command_receipt_status_ck CHECK (
    status IN ('processing', 'completed', 'failed')
  )
);

CREATE TABLE iam_organization (
  organization_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  kind text NOT NULL,
  personal_owner_principal_id uuid,
  name text NOT NULL,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_organization_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_organization_owner_site_fk
    FOREIGN KEY (personal_owner_principal_id, site_id)
    REFERENCES iam_principal(principal_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_organization_organization_site_key UNIQUE (organization_id, site_id),
  CONSTRAINT iam_organization_kind_owner_ck CHECK (
    (kind = 'personal' AND personal_owner_principal_id IS NOT NULL)
    OR (kind = 'team' AND personal_owner_principal_id IS NULL)
  ),
  CONSTRAINT iam_organization_status_ck CHECK (status IN ('active', 'disabled')),
  CONSTRAINT iam_organization_generation_ck CHECK (generation > 0)
);

CREATE UNIQUE INDEX iam_organization_personal_owner_uidx
  ON iam_organization(site_id, personal_owner_principal_id)
  WHERE personal_owner_principal_id IS NOT NULL;

CREATE TABLE iam_membership (
  membership_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  organization_id uuid NOT NULL,
  principal_id uuid NOT NULL,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_membership_organization_site_fk
    FOREIGN KEY (organization_id, site_id)
    REFERENCES iam_organization(organization_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_membership_principal_site_fk
    FOREIGN KEY (principal_id, site_id)
    REFERENCES iam_principal(principal_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_membership_organization_principal_key
    UNIQUE (organization_id, principal_id),
  CONSTRAINT iam_membership_membership_organization_key
    UNIQUE (membership_id, organization_id),
  CONSTRAINT iam_membership_status_ck CHECK (status IN ('active', 'inactive')),
  CONSTRAINT iam_membership_generation_ck CHECK (generation > 0)
);

CREATE TABLE iam_role (
  role_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  organization_id uuid,
  key text NOT NULL,
  name text NOT NULL,
  role_kind text NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_role_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_role_organization_site_fk
    FOREIGN KEY (organization_id, site_id)
    REFERENCES iam_organization(organization_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_role_role_site_key UNIQUE (role_id, site_id),
  CONSTRAINT iam_role_role_organization_key UNIQUE (role_id, organization_id),
  CONSTRAINT iam_role_scope_ck CHECK (
    (role_kind = 'site' AND organization_id IS NULL)
    OR (role_kind = 'organization' AND organization_id IS NOT NULL)
  ),
  CONSTRAINT iam_role_status_ck CHECK (status IN ('active', 'disabled'))
);

CREATE UNIQUE INDEX iam_role_site_key_uidx
  ON iam_role(site_id, key)
  WHERE role_kind = 'site';

CREATE UNIQUE INDEX iam_role_organization_key_uidx
  ON iam_role(organization_id, key)
  WHERE role_kind = 'organization';

CREATE TABLE iam_permission (
  permission_id uuid PRIMARY KEY,
  key text NOT NULL,
  description text NOT NULL,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_permission_key_key UNIQUE (key),
  CONSTRAINT iam_permission_status_ck CHECK (status IN ('active', 'disabled')),
  CONSTRAINT iam_permission_generation_ck CHECK (generation > 0)
);

CREATE TABLE iam_role_permission (
  role_id uuid NOT NULL,
  permission_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_role_permission_pk PRIMARY KEY (role_id, permission_id),
  CONSTRAINT iam_role_permission_role_fk
    FOREIGN KEY (role_id) REFERENCES iam_role(role_id) ON DELETE RESTRICT,
  CONSTRAINT iam_role_permission_permission_fk
    FOREIGN KEY (permission_id) REFERENCES iam_permission(permission_id) ON DELETE RESTRICT
);

CREATE TABLE iam_membership_role (
  organization_id uuid NOT NULL,
  membership_id uuid NOT NULL,
  role_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_membership_role_pk PRIMARY KEY (membership_id, role_id),
  CONSTRAINT iam_membership_role_organization_fk
    FOREIGN KEY (organization_id) REFERENCES iam_organization(organization_id) ON DELETE RESTRICT,
  CONSTRAINT iam_membership_role_membership_organization_fk
    FOREIGN KEY (membership_id, organization_id)
    REFERENCES iam_membership(membership_id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT iam_membership_role_role_organization_fk
    FOREIGN KEY (role_id, organization_id)
    REFERENCES iam_role(role_id, organization_id) ON DELETE RESTRICT
);

CREATE TABLE iam_auth_session (
  auth_session_id uuid PRIMARY KEY,
  principal_scope text NOT NULL,
  site_id uuid,
  organization_id uuid,
  principal_id uuid NOT NULL,
  family_ref uuid NOT NULL,
  family_generation bigint NOT NULL,
  token_hash bytea NOT NULL,
  expires_at timestamptz NOT NULL,
  rotated_to uuid,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_auth_session_principal_fk
    FOREIGN KEY (principal_id) REFERENCES iam_principal(principal_id) ON DELETE RESTRICT,
  CONSTRAINT iam_auth_session_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_auth_session_organization_site_fk
    FOREIGN KEY (organization_id, site_id)
    REFERENCES iam_organization(organization_id, site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_auth_session_rotated_to_fk
    FOREIGN KEY (rotated_to) REFERENCES iam_auth_session(auth_session_id)
    DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT iam_auth_session_family_generation_key
    UNIQUE (family_ref, family_generation),
  CONSTRAINT iam_auth_session_token_hash_key UNIQUE (token_hash),
  CONSTRAINT iam_auth_session_rotated_to_key UNIQUE (rotated_to),
  CONSTRAINT iam_auth_session_scope_ck CHECK (
    (principal_scope = 'site' AND site_id IS NOT NULL)
    OR (principal_scope = 'control_plane' AND site_id IS NULL)
  ),
  CONSTRAINT iam_auth_session_generation_ck CHECK (family_generation > 0),
  CONSTRAINT iam_auth_session_expiry_ck CHECK (expires_at > created_at)
);

CREATE TABLE iam_security_event (
  event_id uuid PRIMARY KEY,
  principal_scope text,
  site_id uuid,
  target_site_id uuid,
  principal_id uuid,
  actor_service text,
  kind text NOT NULL,
  request_id uuid NOT NULL,
  payload jsonb NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT iam_security_event_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_security_event_target_site_fk
    FOREIGN KEY (target_site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT iam_security_event_principal_fk
    FOREIGN KEY (principal_id) REFERENCES iam_principal(principal_id) ON DELETE RESTRICT,
  CONSTRAINT iam_security_event_scope_ck CHECK (
    (principal_id IS NULL AND principal_scope IS NULL AND site_id IS NULL)
    OR (
      principal_id IS NOT NULL
      AND (
        (principal_scope = 'site' AND site_id IS NOT NULL)
        OR (principal_scope = 'control_plane' AND site_id IS NULL)
      )
    )
  ),
  CONSTRAINT iam_security_event_payload_ck CHECK (jsonb_typeof(payload) = 'object')
);

CREATE FUNCTION iam_check_principal_scope()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  principal iam_principal%ROWTYPE;
BEGIN
  SELECT * INTO principal
  FROM iam_principal
  WHERE principal_id = NEW.principal_id;

  IF FOUND AND (
    principal.principal_scope IS DISTINCT FROM NEW.principal_scope
    OR principal.site_id IS DISTINCT FROM NEW.site_id
  ) THEN
    RAISE EXCEPTION 'principal scope does not match referenced principal'
      USING ERRCODE = '23514',
            CONSTRAINT = TG_TABLE_NAME || '_principal_scope_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE FUNCTION iam_reject_principal_identity_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.principal_scope IS DISTINCT FROM OLD.principal_scope
    OR NEW.site_id IS DISTINCT FROM OLD.site_id
    OR NEW.kind IS DISTINCT FROM OLD.kind
  THEN
    RAISE EXCEPTION 'principal scope, site, and kind are immutable'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_principal_identity_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER iam_principal_identity_immutable_trigger
BEFORE UPDATE OF principal_scope, site_id, kind ON iam_principal
FOR EACH ROW EXECUTE FUNCTION iam_reject_principal_identity_update();

CREATE CONSTRAINT TRIGGER iam_identity_principal_scope_trigger
AFTER INSERT OR UPDATE OF principal_scope, site_id, principal_id ON iam_identity
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_principal_scope();

CREATE CONSTRAINT TRIGGER iam_contact_principal_scope_trigger
AFTER INSERT OR UPDATE OF principal_scope, site_id, principal_id ON iam_contact
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_principal_scope();

CREATE CONSTRAINT TRIGGER iam_security_event_principal_scope_trigger
AFTER INSERT OR UPDATE OF principal_scope, site_id, principal_id
ON iam_security_event
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_principal_scope();

CREATE CONSTRAINT TRIGGER iam_auth_session_00_principal_scope_trigger
AFTER INSERT OR UPDATE OF principal_scope, site_id, principal_id ON iam_auth_session
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_principal_scope();

CREATE FUNCTION iam_check_auth_session_organization()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.principal_scope = 'control_plane' THEN
    IF NEW.organization_id IS NOT NULL THEN
      RAISE EXCEPTION 'control-plane session cannot reference an organization'
        USING ERRCODE = '23514',
              CONSTRAINT = 'iam_auth_session_organization_scope_ck';
    END IF;
  ELSE
    IF NEW.organization_id IS NOT NULL THEN
      PERFORM membership_id
      FROM iam_membership
      WHERE organization_id = NEW.organization_id
        AND site_id = NEW.site_id
        AND principal_id = NEW.principal_id
        AND status = 'active'
      FOR SHARE;
    END IF;
    IF NEW.organization_id IS NULL OR NOT FOUND THEN
      RAISE EXCEPTION 'site session requires an active same-site membership'
        USING ERRCODE = '23514',
              CONSTRAINT = 'iam_auth_session_organization_scope_ck';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER iam_auth_session_organization_scope_trigger
AFTER INSERT OR UPDATE OF principal_scope, site_id, organization_id, principal_id
ON iam_auth_session
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_auth_session_organization();

CREATE FUNCTION iam_check_membership_live_auth_sessions()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  membership iam_membership%ROWTYPE;
BEGIN
  membership := OLD;
  IF EXISTS (
    SELECT 1
    FROM iam_auth_session session
    WHERE session.principal_scope = 'site'
      AND session.site_id = membership.site_id
      AND session.organization_id = membership.organization_id
      AND session.principal_id = membership.principal_id
      AND session.revoked_at IS NULL
      AND session.expires_at > now()
  ) AND (
    TG_OP = 'DELETE'
    OR NEW.status <> 'active'
    OR NEW.site_id IS DISTINCT FROM OLD.site_id
    OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
    OR NEW.principal_id IS DISTINCT FROM OLD.principal_id
  ) THEN
    RAISE EXCEPTION 'live auth session requires its active membership'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_membership_live_auth_session_ck';
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;

CREATE CONSTRAINT TRIGGER iam_membership_live_auth_session_update_trigger
AFTER UPDATE OF status, site_id, organization_id, principal_id
ON iam_membership
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_membership_live_auth_sessions();

CREATE CONSTRAINT TRIGGER iam_membership_live_auth_session_delete_trigger
AFTER DELETE ON iam_membership
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_membership_live_auth_sessions();

CREATE FUNCTION iam_reject_command_receipt_claim_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.command_id IS DISTINCT FROM OLD.command_id
    OR NEW.command_kind IS DISTINCT FROM OLD.command_kind
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
  THEN
    RAISE EXCEPTION 'command receipt claim identity is immutable'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_command_receipt_claim_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER iam_command_receipt_claim_immutable_trigger
BEFORE UPDATE OF command_id, command_kind, request_digest
ON iam_command_receipt
FOR EACH ROW EXECUTE FUNCTION iam_reject_command_receipt_claim_update();

CREATE FUNCTION iam_reject_auth_session_identity_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.principal_scope IS DISTINCT FROM OLD.principal_scope
    OR NEW.site_id IS DISTINCT FROM OLD.site_id
    OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
    OR NEW.principal_id IS DISTINCT FROM OLD.principal_id
    OR NEW.family_ref IS DISTINCT FROM OLD.family_ref
    OR NEW.token_hash IS DISTINCT FROM OLD.token_hash
  THEN
    RAISE EXCEPTION 'auth session security identity is immutable'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_auth_session_identity_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER iam_auth_session_identity_immutable_trigger
BEFORE UPDATE OF principal_scope, site_id, organization_id, principal_id,
  family_ref, token_hash
ON iam_auth_session
FOR EACH ROW EXECUTE FUNCTION iam_reject_auth_session_identity_update();

CREATE FUNCTION iam_reject_auth_session_rotation_unlink()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF OLD.rotated_to IS NOT NULL
    AND NEW.rotated_to IS DISTINCT FROM OLD.rotated_to
  THEN
    RAISE EXCEPTION 'auth session rotation link is immutable once set'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_auth_session_rotation_link_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER iam_auth_session_rotation_link_immutable_trigger
BEFORE UPDATE OF rotated_to ON iam_auth_session
FOR EACH ROW EXECUTE FUNCTION iam_reject_auth_session_rotation_unlink();

CREATE FUNCTION iam_reject_auth_session_generation_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.family_generation IS DISTINCT FROM OLD.family_generation THEN
    RAISE EXCEPTION 'auth session family generation is immutable'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_auth_session_family_generation_immutable_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER iam_auth_session_family_generation_immutable_trigger
BEFORE UPDATE OF family_generation ON iam_auth_session
FOR EACH ROW EXECUTE FUNCTION iam_reject_auth_session_generation_update();

CREATE FUNCTION iam_check_auth_session_rotation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.rotated_to IS NOT NULL AND NOT EXISTS (
    SELECT 1
    FROM iam_auth_session successor
    WHERE successor.auth_session_id = NEW.rotated_to
      AND successor.family_ref = NEW.family_ref
      AND successor.family_generation = NEW.family_generation + 1
      AND successor.principal_scope = NEW.principal_scope
      AND successor.site_id IS NOT DISTINCT FROM NEW.site_id
      AND successor.organization_id IS NOT DISTINCT FROM NEW.organization_id
      AND successor.principal_id = NEW.principal_id
  ) THEN
    RAISE EXCEPTION 'auth session rotation must advance exactly one generation'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_auth_session_rotation_monotonic_ck';
  END IF;
  IF NEW.family_generation > 1 AND NOT EXISTS (
    SELECT 1
    FROM iam_auth_session predecessor
    WHERE predecessor.family_ref = NEW.family_ref
      AND predecessor.family_generation = NEW.family_generation - 1
      AND predecessor.rotated_to = NEW.auth_session_id
      AND predecessor.principal_scope = NEW.principal_scope
      AND predecessor.site_id IS NOT DISTINCT FROM NEW.site_id
      AND predecessor.organization_id IS NOT DISTINCT FROM NEW.organization_id
      AND predecessor.principal_id = NEW.principal_id
  ) THEN
    RAISE EXCEPTION 'auth session successor requires its immediate predecessor'
      USING ERRCODE = '23514',
            CONSTRAINT = 'iam_auth_session_rotation_monotonic_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER iam_auth_session_rotation_monotonic_trigger
AFTER INSERT OR UPDATE OF rotated_to, family_ref, family_generation
ON iam_auth_session
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION iam_check_auth_session_rotation();

-- source: database/schema/30-chat.sql
-- sha256: d312a11600458cd9a0bb49327c287b6f966fd714efc91324f06d73e3ebc3cc16
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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

-- source: database/schema/40-agent.sql
-- sha256: 2efc60bbb44e3776b9bdd839c6b0e7d4c6aebbe0d44bd798b9d419325c575467
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
  status text NOT NULL,
  applied_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_control_inbox_run_command_key UNIQUE (agent_run_id, command_id),
  CONSTRAINT agent_control_inbox_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_control_inbox_status_ck
    CHECK (status IN ('pending','applied','rejected','failed')),
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
    RETURN NEW;
  END IF;
  IF NEW.control_id IS DISTINCT FROM OLD.control_id
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.command_id IS DISTINCT FROM OLD.command_id
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
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

-- source: database/schema/45-langgraph-checkpointer.sql
-- sha256: 1921ae91738c40a9cbb6f4c993a49190552d7145a762a2f425230e833a630a6a
-- Normalized body SHA-256: b925febf5ef411feb7e1f7e32261760b89dc84a93975cc7776d6bc02086dc6f1
-- Source: langgraph-checkpoint-postgres==3.1.0 AsyncPostgresSaver.setup()
-- Captured with PostgreSQL 18.4; normalized from explicit four-table pg_dump.
-- Runtime must not call setup(); Root owns this deterministic baseline segment.
SET search_path TO kokoro, pg_catalog;

CREATE TABLE checkpoint_blobs (
  thread_id text NOT NULL,
  checkpoint_ns text DEFAULT ''::text NOT NULL,
  channel text NOT NULL,
  version text NOT NULL,
  type text NOT NULL,
  blob bytea,
  CONSTRAINT checkpoint_blobs_pkey
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

CREATE TABLE checkpoint_migrations (
  v integer NOT NULL,
  CONSTRAINT checkpoint_migrations_pkey PRIMARY KEY (v)
);

CREATE TABLE checkpoint_writes (
  thread_id text NOT NULL,
  checkpoint_ns text DEFAULT ''::text NOT NULL,
  checkpoint_id text NOT NULL,
  task_id text NOT NULL,
  idx integer NOT NULL,
  channel text NOT NULL,
  type text,
  blob bytea NOT NULL,
  task_path text DEFAULT ''::text NOT NULL,
  CONSTRAINT checkpoint_writes_pkey
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);

CREATE TABLE checkpoints (
  thread_id text NOT NULL,
  checkpoint_ns text DEFAULT ''::text NOT NULL,
  checkpoint_id text NOT NULL,
  parent_checkpoint_id text,
  type text,
  checkpoint jsonb NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
  CONSTRAINT checkpoints_pkey
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE INDEX checkpoint_blobs_thread_id_idx ON checkpoint_blobs(thread_id);
CREATE INDEX checkpoint_writes_thread_id_idx ON checkpoint_writes(thread_id);
CREATE INDEX checkpoints_thread_id_idx ON checkpoints(thread_id);

INSERT INTO checkpoint_migrations(v)
VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9);

-- source: database/schema/50-capability.sql
-- sha256: d04e810a0248c28e91806d87171b0b825c9586a59149166b844da1f9d209846f
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
RETURNS trigger LANGUAGE plpgsql AS $$
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
RETURNS trigger LANGUAGE plpgsql AS $$
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

-- source: database/schema/60-model.sql
-- sha256: 9be94a3691aa6527b048a8336682d1ad5d822bf02c1380e3ffd5087d76fabb9c
SET search_path TO kokoro, pg_catalog;

CREATE TABLE model_provider (
  provider_id uuid PRIMARY KEY,
  key text NOT NULL,
  display_name text NOT NULL,
  status text NOT NULL,
  secret_handle_ref text,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT model_provider_key_key UNIQUE (key),
  CONSTRAINT model_provider_status_ck CHECK (status IN ('active','disabled')),
  CONSTRAINT model_provider_no_inference_secret_ck CHECK (secret_handle_ref IS NULL),
  CONSTRAINT model_provider_generation_ck CHECK (generation > 0)
);

CREATE TABLE model_definition (
  model_id uuid PRIMARY KEY,
  key text NOT NULL,
  display_name text NOT NULL,
  status text NOT NULL,
  current_revision_id uuid,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT model_definition_key_key UNIQUE (key),
  CONSTRAINT model_definition_model_revision_key UNIQUE (model_id, current_revision_id),
  CONSTRAINT model_definition_status_ck CHECK (status IN ('active','disabled')),
  CONSTRAINT model_definition_generation_ck CHECK (generation > 0)
);

CREATE TABLE model_revision (
  model_revision_id uuid PRIMARY KEY,
  model_id uuid NOT NULL,
  revision integer NOT NULL,
  provider_id uuid NOT NULL,
  provider_model_name text NOT NULL,
  transport text NOT NULL,
  modalities jsonb NOT NULL,
  context_window integer NOT NULL,
  published_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT model_revision_revision_model_key UNIQUE (model_revision_id, model_id),
  CONSTRAINT model_revision_model_revision_key UNIQUE (model_id, revision),
  CONSTRAINT model_revision_model_fk
    FOREIGN KEY (model_id) REFERENCES model_definition(model_id) ON DELETE RESTRICT,
  CONSTRAINT model_revision_provider_fk
    FOREIGN KEY (provider_id) REFERENCES model_provider(provider_id) ON DELETE RESTRICT,
  CONSTRAINT model_revision_revision_ck CHECK (revision > 0),
  CONSTRAINT model_revision_transport_ck CHECK (transport IN ('litellm','direct','local')),
  CONSTRAINT model_revision_modalities_ck CHECK (
    jsonb_typeof(modalities) = 'array' AND jsonb_array_length(modalities) > 0
  ),
  CONSTRAINT model_revision_context_window_ck CHECK (context_window > 0)
);

ALTER TABLE model_definition
  ADD CONSTRAINT model_definition_current_revision_fk
  FOREIGN KEY (current_revision_id, model_id)
  REFERENCES model_revision(model_revision_id, model_id)
  DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE model_routing_policy (
  routing_policy_id uuid PRIMARY KEY,
  site_id uuid NOT NULL,
  label text NOT NULL,
  model_revision_id uuid NOT NULL,
  priority integer NOT NULL,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT model_routing_policy_site_fk
    FOREIGN KEY (site_id) REFERENCES site_site(site_id) ON DELETE RESTRICT,
  CONSTRAINT model_routing_policy_revision_fk
    FOREIGN KEY (model_revision_id) REFERENCES model_revision(model_revision_id) ON DELETE RESTRICT,
  CONSTRAINT model_routing_policy_site_label_priority_key
    UNIQUE (site_id, label, priority),
  CONSTRAINT model_routing_policy_priority_ck CHECK (priority >= 0),
  CONSTRAINT model_routing_policy_status_ck CHECK (status IN ('active','disabled')),
  CONSTRAINT model_routing_policy_generation_ck CHECK (generation > 0)
);

CREATE TABLE model_provider_health_state (
  provider_id uuid PRIMARY KEY,
  status text NOT NULL,
  generation bigint NOT NULL DEFAULT 1,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT model_provider_health_state_provider_fk
    FOREIGN KEY (provider_id) REFERENCES model_provider(provider_id) ON DELETE RESTRICT,
  CONSTRAINT model_provider_health_state_slice_a_status_ck CHECK (status = 'unknown'),
  CONSTRAINT model_provider_health_state_generation_ck CHECK (generation > 0)
);

CREATE FUNCTION model_validate_current_revision()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE revision_published_at timestamptz;
DECLARE revision_transport text;
BEGIN
  IF NEW.current_revision_id IS NULL THEN
    RETURN NULL;
  END IF;
  SELECT published_at, transport
  INTO revision_published_at, revision_transport
  FROM model_revision
  WHERE model_revision_id = NEW.current_revision_id AND model_id = NEW.model_id;
  IF revision_published_at IS NULL OR revision_transport <> 'litellm' THEN
    RAISE EXCEPTION 'current model revision must be published and LiteLLM'
      USING ERRCODE='23514', CONSTRAINT='model_definition_current_published_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER model_definition_current_revision_trigger
AFTER INSERT OR UPDATE OF current_revision_id ON model_definition
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION model_validate_current_revision();

CREATE FUNCTION model_validate_routing_target()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE revision_published_at timestamptz;
DECLARE revision_transport text;
BEGIN
  IF NEW.status <> 'active' THEN
    RETURN NULL;
  END IF;
  SELECT published_at, transport
  INTO revision_published_at, revision_transport
  FROM model_revision
  WHERE model_revision_id = NEW.model_revision_id;
  IF revision_published_at IS NULL OR revision_transport <> 'litellm' THEN
    RAISE EXCEPTION 'active routing policy requires a published LiteLLM revision'
      USING ERRCODE='23514', CONSTRAINT='model_routing_policy_published_litellm_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER model_routing_policy_target_trigger
AFTER INSERT OR UPDATE OF model_revision_id, status ON model_routing_policy
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION model_validate_routing_target();

CREATE FUNCTION model_validate_revision_routes()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM model_routing_policy
    WHERE model_revision_id = NEW.model_revision_id AND status = 'active'
  ) AND (NEW.published_at IS NULL OR NEW.transport <> 'litellm')
  THEN
    RAISE EXCEPTION 'routed model revision must remain published and LiteLLM'
      USING ERRCODE='23514', CONSTRAINT='model_revision_live_route_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER model_revision_live_route_trigger
AFTER UPDATE OF published_at, transport ON model_revision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION model_validate_revision_routes();

CREATE FUNCTION model_reject_published_revision_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.published_at IS NOT NULL AND (TG_OP = 'DELETE' OR
    NEW.model_id IS DISTINCT FROM OLD.model_id
    OR NEW.revision IS DISTINCT FROM OLD.revision
    OR NEW.provider_id IS DISTINCT FROM OLD.provider_id
    OR NEW.provider_model_name IS DISTINCT FROM OLD.provider_model_name
    OR NEW.transport IS DISTINCT FROM OLD.transport
    OR NEW.modalities IS DISTINCT FROM OLD.modalities
    OR NEW.context_window IS DISTINCT FROM OLD.context_window
    OR NEW.published_at IS DISTINCT FROM OLD.published_at
  ) THEN
    RAISE EXCEPTION 'published model revision is immutable'
      USING ERRCODE='23514', CONSTRAINT='model_revision_published_immutable_ck';
  END IF;
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;

CREATE TRIGGER model_revision_published_immutable_trigger
BEFORE UPDATE OR DELETE ON model_revision
FOR EACH ROW EXECUTE FUNCTION model_reject_published_revision_update();

-- source: database/schema/99-cross-capability-relations.sql
-- sha256: 20db03a7c653b52b52a7b3778432254dfacd931021d6e86739cc255fdd0343e5
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
