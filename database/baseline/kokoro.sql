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
-- sha256: 4085fa1f786bdd8356e9b2865442b6588f536d77dbc1e9983d8eb3c0b9e6efb6
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
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
-- sha256: a80ac4138ea5eab741e105488aa235eb2d99225167161c5e26837aada98e443e
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

-- source: database/schema/40-agent.sql
-- sha256: 0aae75be89b474440f2fbb520709652650a9a2d8468207ad1a894e4a32ef9f15
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
  usage_input_tokens bigint NOT NULL DEFAULT 0,
  usage_output_tokens bigint NOT NULL DEFAULT 0,
  usage_cached_tokens bigint NOT NULL DEFAULT 0,
  usage_call_count bigint NOT NULL DEFAULT 0,
  budget_tokens_used bigint NOT NULL DEFAULT 0,
  terminal_claim_id uuid,
  terminal_claim_epoch bigint,
  terminal_claim_lease_generation bigint,
  terminal_claimed_at timestamptz,
  terminal_at timestamptz,
  runtime_compacted_at timestamptz,
  runtime_compaction_policy_version integer,
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
  CONSTRAINT agent_run_generation_ck CHECK (generation > 0),
  CONSTRAINT agent_run_usage_accumulator_nonnegative_ck CHECK (
    usage_input_tokens >= 0 AND usage_output_tokens >= 0
    AND usage_cached_tokens >= 0 AND usage_call_count >= 0
    AND budget_tokens_used >= 0
  ),
  CONSTRAINT agent_run_terminal_claim_group_ck CHECK (
    (terminal_claim_id IS NULL AND terminal_claim_epoch IS NULL
      AND terminal_claim_lease_generation IS NULL AND terminal_claimed_at IS NULL)
    OR
    (terminal_claim_id IS NOT NULL AND terminal_claim_epoch IS NOT NULL
      AND terminal_claim_epoch > 0
      AND terminal_claim_lease_generation IS NOT NULL
      AND terminal_claim_lease_generation > 0 AND terminal_claimed_at IS NOT NULL)
  ),
  CONSTRAINT agent_run_runtime_compaction_group_ck CHECK (
    (runtime_compacted_at IS NULL AND runtime_compaction_policy_version IS NULL)
    OR (runtime_compacted_at IS NOT NULL
      AND runtime_compaction_policy_version IS NOT NULL
      AND runtime_compaction_policy_version > 0
      AND terminal_at IS NOT NULL AND runtime_compacted_at > terminal_at)
  )
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
  usage_feature_key text NOT NULL DEFAULT 'agent',
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
    CHECK (jsonb_typeof(payload) = 'object'),
  CONSTRAINT agent_execution_manifest_usage_feature_key_ck
    CHECK (usage_feature_key <> '' AND octet_length(usage_feature_key) <= 128)
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
  stream_index bigint,
  stream_timestamp_ms bigint,
  kind text NOT NULL,
  schema_version integer NOT NULL,
  payload jsonb NOT NULL,
  published_at timestamptz,
  last_publish_attempt_at timestamptz,
  publish_attempt bigint NOT NULL DEFAULT 0,
  acked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_event_outbox_run_seq_key UNIQUE (agent_run_id, seq),
  CONSTRAINT agent_event_outbox_run_stream_index_key
    UNIQUE (agent_run_id, stream_index),
  CONSTRAINT agent_event_outbox_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_event_outbox_epoch_ck CHECK (epoch > 0),
  CONSTRAINT agent_event_outbox_seq_ck CHECK (seq > 0),
  CONSTRAINT agent_event_outbox_stream_metadata_group_ck CHECK (
    (stream_index IS NULL AND stream_timestamp_ms IS NULL)
    OR (stream_index IS NOT NULL AND stream_index >= 0
      AND stream_timestamp_ms IS NOT NULL AND stream_timestamp_ms > 0)
  ),
  CONSTRAINT agent_event_outbox_schema_version_ck CHECK (schema_version > 0),
  CONSTRAINT agent_event_outbox_publish_attempt_ck CHECK (
    (publish_attempt = 0 AND last_publish_attempt_at IS NULL AND published_at IS NULL)
    OR (publish_attempt > 0 AND last_publish_attempt_at IS NOT NULL
      AND published_at IS NOT NULL
      AND last_publish_attempt_at >= published_at)
  ),
  CONSTRAINT agent_event_outbox_payload_ck
    CHECK (jsonb_typeof(payload) IN ('object','array'))
);

CREATE INDEX agent_event_outbox_run_epoch_seq_idx
  ON agent_event_outbox(agent_run_id, epoch, seq);

CREATE UNIQUE INDEX agent_event_outbox_one_terminal_idx
  ON agent_event_outbox(agent_run_id)
  WHERE kind IN ('run.completed','run.failed');

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
  rejected_seq bigint,
  rejection_code text,
  rejected_at timestamptz,
  generation bigint NOT NULL DEFAULT 1,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_projection_ack_pk PRIMARY KEY (agent_run_id, consumer),
  CONSTRAINT agent_projection_ack_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_projection_ack_consumer_ck CHECK (consumer = 'chat'),
  CONSTRAINT agent_projection_ack_epoch_ck CHECK (projected_epoch > 0),
  CONSTRAINT agent_projection_ack_seq_ck CHECK (projected_seq >= 0),
  CONSTRAINT agent_projection_ack_rejection_group_ck CHECK (
    (rejected_seq IS NULL AND rejection_code IS NULL AND rejected_at IS NULL)
    OR (rejected_seq IS NOT NULL AND rejected_seq > 0
      AND rejection_code IS NOT NULL AND rejection_code <> ''
      AND octet_length(rejection_code) <= 128 AND rejected_at IS NOT NULL)
  ),
  CONSTRAINT agent_projection_ack_close_ck CHECK (
    NOT consumer_closed OR producer_close_requested
  ),
  CONSTRAINT agent_projection_ack_generation_ck CHECK (generation > 0)
);

CREATE TABLE agent_tool_effect (
  effect_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  tool_call_id text NOT NULL,
  tool_name text,
  effect_kind text NOT NULL,
  request_digest bytea NOT NULL,
  status text NOT NULL,
  claim_epoch bigint,
  claim_lease_generation bigint,
  result_digest bytea,
  result_schema_version integer,
  result_payload jsonb,
  result_is_error boolean,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_tool_effect_identity_key
    UNIQUE (agent_run_id, tool_call_id, effect_kind),
  CONSTRAINT agent_tool_effect_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_tool_effect_status_ck
    CHECK (status IN ('claimed','completed','failed','unknown')),
  CONSTRAINT agent_tool_effect_claim_fence_group_ck CHECK (
    claim_epoch IS NOT NULL AND claim_epoch > 0
    AND claim_lease_generation IS NOT NULL AND claim_lease_generation > 0
  ),
  CONSTRAINT agent_tool_effect_tool_name_ck CHECK (
    (effect_kind = 'tool_journal' AND tool_name IS NOT NULL AND tool_name <> ''
      AND octet_length(tool_name) <= 256)
    OR (effect_kind <> 'tool_journal' AND tool_name IS NULL)
  ),
  CONSTRAINT agent_tool_effect_result_ck CHECK (
    (status IN ('claimed','unknown','failed') AND result_digest IS NULL
      AND result_schema_version IS NULL AND result_payload IS NULL
      AND result_is_error IS NULL)
    OR (status = 'completed' AND result_digest IS NOT NULL
      AND octet_length(result_digest) = 32
      AND result_schema_version IS NOT NULL AND result_schema_version > 0
      AND result_payload IS NOT NULL
      AND jsonb_typeof(result_payload) = 'string'
      AND octet_length(result_payload::text) <= 65536
      AND result_is_error IS NOT NULL)
  )
);

CREATE TABLE agent_run_usage (
  run_usage_id uuid PRIMARY KEY,
  agent_run_id uuid NOT NULL,
  digest bytea NOT NULL,
  input_tokens bigint NOT NULL,
  output_tokens bigint NOT NULL,
  cached_tokens bigint NOT NULL,
  call_count bigint NOT NULL,
  finalized_at timestamptz NOT NULL,
  CONSTRAINT agent_run_usage_run_key UNIQUE (agent_run_id),
  CONSTRAINT agent_run_usage_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_run_usage_digest_ck CHECK (octet_length(digest) = 32),
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
  call_count bigint NOT NULL,
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
  source_key text NOT NULL,
  raw_hash bytea NOT NULL,
  request_digest bytea NOT NULL,
  error_code text NOT NULL,
  payload jsonb NOT NULL,
  retry_status text NOT NULL,
  claim_generation bigint NOT NULL DEFAULT 1,
  claimed_by text,
  claimed_at timestamptz,
  claim_expires_at timestamptz,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agent_dispatch_dlq_run_fk
    FOREIGN KEY (agent_run_id) REFERENCES agent_run(agent_run_id) ON DELETE RESTRICT,
  CONSTRAINT agent_dispatch_dlq_source_hash_key UNIQUE (source_key, raw_hash),
  CONSTRAINT agent_dispatch_dlq_source_key_ck
    CHECK (source_key <> '' AND octet_length(source_key) <= 512),
  CONSTRAINT agent_dispatch_dlq_raw_hash_ck CHECK (octet_length(raw_hash) = 32),
  CONSTRAINT agent_dispatch_dlq_payload_ck CHECK (
    jsonb_typeof(payload) = 'object' AND octet_length(payload::text) <= 65536
  ),
  CONSTRAINT agent_dispatch_dlq_retry_status_ck
    CHECK (retry_status IN ('pending','retrying','resolved','abandoned')),
  CONSTRAINT agent_dispatch_dlq_claim_generation_ck CHECK (claim_generation > 0),
  CONSTRAINT agent_dispatch_dlq_claim_state_ck CHECK (
    (retry_status = 'pending' AND claimed_by IS NULL AND claimed_at IS NULL
      AND claim_expires_at IS NULL AND resolved_at IS NULL)
    OR (retry_status = 'retrying' AND claimed_by IS NOT NULL AND claimed_by <> ''
      AND octet_length(claimed_by) <= 256 AND claimed_at IS NOT NULL
      AND claim_expires_at IS NOT NULL AND claim_expires_at > claimed_at
      AND resolved_at IS NULL)
    OR (retry_status IN ('resolved','abandoned')
      AND claimed_by IS NOT NULL AND claimed_by <> ''
      AND octet_length(claimed_by) <= 256 AND claimed_at IS NOT NULL
      AND claim_expires_at IS NOT NULL AND claim_expires_at > claimed_at
      AND resolved_at IS NOT NULL)
  )
);

CREATE INDEX agent_dispatch_dlq_retry_idx
  ON agent_dispatch_dlq(retry_status, claim_expires_at);

COMMENT ON TABLE agent_control_inbox IS
  'A mature superseded control outcome is persisted as the existing rejected status; superseded is not a second durable state. Control application is owned by the exact current live agent_run_lease; paused runs must first adopt a new lease. DECIDE fingerprint resolution occurs synchronously before first INSERT.';

COMMENT ON TABLE agent_run_lease IS
  'The sole durable worker claim for dispatch consumption, execution, and control application. Dispatch claim atomically moves queued to running and creates this lease; expired leases are reclaimed by generation CAS.';

COMMENT ON TABLE agent_dispatch_outbox IS
  'Dispatcher publication claims use attempt as the CAS generation and next_attempt_at as the finite network-I/O lease deadline. attempt advances before I/O; success CASes the same attempt to dispatched_at; exhaustion records DLQ evidence and terminal failure in one transaction.';

CREATE FUNCTION agent_validate_run_manifest_state()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE lease_generation bigint;
DECLARE lease_deadline timestamptz;
DECLARE terminal_states CONSTANT text[] := ARRAY[
  'completed','failed','cancelled','admission_failed'
];
DECLARE runtime_terminal_states CONSTANT text[] := ARRAY[
  'completed','failed','cancelled'
];
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
  IF OLD.state = ANY (terminal_states) AND (
    NEW.state IS DISTINCT FROM OLD.state
    OR NEW.execution_manifest_id IS DISTINCT FROM OLD.execution_manifest_id
    OR NEW.epoch IS DISTINCT FROM OLD.epoch
    OR NEW.next_event_seq IS DISTINCT FROM OLD.next_event_seq
    OR NEW.usage_input_tokens IS DISTINCT FROM OLD.usage_input_tokens
    OR NEW.usage_output_tokens IS DISTINCT FROM OLD.usage_output_tokens
    OR NEW.usage_cached_tokens IS DISTINCT FROM OLD.usage_cached_tokens
    OR NEW.usage_call_count IS DISTINCT FROM OLD.usage_call_count
    OR NEW.budget_tokens_used IS DISTINCT FROM OLD.budget_tokens_used
    OR NEW.terminal_claim_id IS DISTINCT FROM OLD.terminal_claim_id
    OR NEW.terminal_claim_epoch IS DISTINCT FROM OLD.terminal_claim_epoch
    OR NEW.terminal_claim_lease_generation IS DISTINCT FROM OLD.terminal_claim_lease_generation
    OR NEW.terminal_claimed_at IS DISTINCT FROM OLD.terminal_claimed_at
    OR NEW.terminal_at IS DISTINCT FROM OLD.terminal_at
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
  IF NEW.usage_input_tokens < OLD.usage_input_tokens
    OR NEW.usage_output_tokens < OLD.usage_output_tokens
    OR NEW.usage_cached_tokens < OLD.usage_cached_tokens
    OR NEW.usage_call_count < OLD.usage_call_count
    OR NEW.budget_tokens_used < OLD.budget_tokens_used
  THEN
    RAISE EXCEPTION 'run usage accumulator cannot regress'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_accumulator_monotonic_ck';
  END IF;
  IF NOT (OLD.state = ANY (terminal_states))
    AND NOT (NEW.state = ANY (terminal_states))
    AND NEW.terminal_at IS NOT NULL
  THEN
    RAISE EXCEPTION 'preterminal run cannot have a terminal timestamp'
      USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_at_state_ck';
  END IF;
  IF NEW.state = ANY (terminal_states)
    AND NEW.terminal_at IS NULL
  THEN
    RAISE EXCEPTION 'terminal run requires a terminal timestamp'
      USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_at_state_ck';
  END IF;
  IF NEW.runtime_compacted_at IS DISTINCT FROM OLD.runtime_compacted_at
    OR NEW.runtime_compaction_policy_version
      IS DISTINCT FROM OLD.runtime_compaction_policy_version
  THEN
    IF NOT (OLD.state = ANY (terminal_states)) THEN
      RAISE EXCEPTION 'only a previously terminal run can be runtime compacted'
        USING ERRCODE='23514', CONSTRAINT='agent_run_runtime_compaction_terminal_ck';
    END IF;
    IF OLD.runtime_compacted_at IS NOT NULL
      OR NEW.runtime_compacted_at IS NULL
      OR NEW.runtime_compacted_at IS DISTINCT FROM transaction_timestamp()
    THEN
      RAISE EXCEPTION 'runtime compaction is a one-time transaction-bound mark'
        USING ERRCODE='23514', CONSTRAINT='agent_run_runtime_compaction_once_ck';
    END IF;
  END IF;

  IF NEW.terminal_claim_id IS DISTINCT FROM OLD.terminal_claim_id
    OR NEW.terminal_claim_epoch IS DISTINCT FROM OLD.terminal_claim_epoch
    OR NEW.terminal_claim_lease_generation IS DISTINCT FROM OLD.terminal_claim_lease_generation
    OR NEW.terminal_claimed_at IS DISTINCT FROM OLD.terminal_claimed_at
  THEN
    IF NEW.terminal_claim_id IS NULL THEN
      RAISE EXCEPTION 'terminal reservation cannot be cleared'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_one_way_ck';
    END IF;
    IF OLD.terminal_claim_id IS NOT NULL
      AND NEW.terminal_claim_epoch <= OLD.terminal_claim_epoch
    THEN
      RAISE EXCEPTION 'terminal reservation is immutable inside an epoch'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_one_way_ck';
    END IF;
    IF NEW.terminal_claim_epoch <> NEW.epoch
      OR NEW.terminal_claimed_at IS DISTINCT FROM transaction_timestamp()
    THEN
      RAISE EXCEPTION 'terminal reservation must use the current run epoch and transaction'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_fence_ck';
    END IF;
    SELECT generation, leased_until INTO lease_generation, lease_deadline
    FROM agent_run_lease WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
    IF lease_generation IS NULL
      OR lease_generation <> NEW.terminal_claim_lease_generation
      OR lease_deadline <= transaction_timestamp()
    THEN
      RAISE EXCEPTION 'terminal reservation requires the current live lease generation'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_fence_ck';
    END IF;
  END IF;

  IF NEW.state = 'admission_failed' AND OLD.state <> ALL (terminal_states) THEN
    IF NEW.execution_manifest_id IS NOT NULL
      OR NEW.terminal_claim_id IS NOT NULL
      OR NEW.terminal_claim_epoch IS NOT NULL
      OR NEW.terminal_claim_lease_generation IS NOT NULL
      OR NEW.terminal_claimed_at IS NOT NULL
    THEN
      RAISE EXCEPTION 'admission failure must precede manifest and runtime reservation'
        USING ERRCODE='23514', CONSTRAINT='agent_run_admission_failure_boundary_ck';
    END IF;
    IF NEW.terminal_at IS DISTINCT FROM transaction_timestamp() THEN
      RAISE EXCEPTION 'admission failure timestamp must bind its transaction'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_transaction_ck';
    END IF;
  ELSIF NEW.state = ANY (runtime_terminal_states)
    AND OLD.state <> ALL (terminal_states)
  THEN
    IF OLD.terminal_claim_id IS NULL
      OR NEW.terminal_claim_id IS DISTINCT FROM OLD.terminal_claim_id
      OR NEW.terminal_claim_epoch IS DISTINCT FROM NEW.epoch
    THEN
      RAISE EXCEPTION 'terminal transition requires its existing current reservation'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_required_ck';
    END IF;
    SELECT generation, leased_until INTO lease_generation, lease_deadline
    FROM agent_run_lease WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
    IF lease_generation IS DISTINCT FROM NEW.terminal_claim_lease_generation
      OR lease_deadline <= transaction_timestamp()
    THEN
      RAISE EXCEPTION 'stale terminal claimant cannot finalize the run'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_fence_ck';
    END IF;
    IF NEW.terminal_at IS DISTINCT FROM transaction_timestamp() THEN
      RAISE EXCEPTION 'terminal transition timestamp must bind its transaction'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_transaction_ck';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_run_identity_terminal_trigger
BEFORE UPDATE OF launch_id, launch_request_digest, namespace, execution_manifest_id,
  state, epoch, next_event_seq, usage_input_tokens, usage_output_tokens,
  usage_cached_tokens, usage_call_count, budget_tokens_used,
  terminal_claim_id, terminal_claim_epoch,
  terminal_claim_lease_generation, terminal_claimed_at, terminal_at,
  runtime_compacted_at, runtime_compaction_policy_version
ON agent_run
FOR EACH ROW EXECUTE FUNCTION agent_reject_run_identity_or_terminal_update();

CREATE FUNCTION agent_reject_run_delete()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  RAISE EXCEPTION 'agent run launch identity and replay evidence cannot be deleted'
    USING ERRCODE='23514', CONSTRAINT='agent_run_identity_delete_ck';
END;
$$;

CREATE TRIGGER agent_run_identity_delete_trigger
BEFORE DELETE ON agent_run
FOR EACH ROW EXECUTE FUNCTION agent_reject_run_delete();

CREATE FUNCTION agent_validate_event_cursor_allocation()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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

CREATE FUNCTION agent_validate_terminal_run_completion()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE terminal_event_count integer;
DECLARE usage_count integer;
DECLARE lease_count integer;
DECLARE manifest_count integer;
DECLARE current_lease_generation bigint;
DECLARE current_lease_deadline timestamptz;
BEGIN
  IF NEW.state IN ('completed','failed','cancelled') THEN
    IF NEW.terminal_claim_id IS NULL
      OR NEW.terminal_claim_epoch IS DISTINCT FROM NEW.epoch
      OR NEW.terminal_at IS NULL
    THEN
      RAISE EXCEPTION 'terminal run requires a durable current reservation'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_required_ck';
    END IF;
    SELECT generation, leased_until
    INTO current_lease_generation, current_lease_deadline
    FROM agent_run_lease WHERE agent_run_id = NEW.agent_run_id;
    IF current_lease_generation IS DISTINCT FROM NEW.terminal_claim_lease_generation
      OR current_lease_deadline <= transaction_timestamp()
      OR NEW.terminal_at IS DISTINCT FROM transaction_timestamp()
    THEN
      RAISE EXCEPTION 'terminal run requires its current live lease in the same transaction'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_claim_fence_ck';
    END IF;
    SELECT count(*) INTO terminal_event_count
    FROM agent_event_outbox
    WHERE agent_run_id = NEW.agent_run_id
      AND epoch = NEW.terminal_claim_epoch
      AND seq = NEW.next_event_seq - 1
      AND kind = CASE
        WHEN NEW.state IN ('completed','cancelled') THEN 'run.completed'
        ELSE 'run.failed'
      END
      AND created_at IS NOT DISTINCT FROM NEW.terminal_at;
    IF terminal_event_count <> 1 THEN
      RAISE EXCEPTION 'terminal state requires its terminal event in the same transaction'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_event_complete_ck';
    END IF;
    SELECT count(*) INTO usage_count
    FROM agent_run_usage WHERE agent_run_id = NEW.agent_run_id;
    IF usage_count <> 1 THEN
      RAISE EXCEPTION 'terminal state requires exactly one finalized usage aggregate'
        USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_usage_complete_ck';
    END IF;
  ELSIF NEW.state = 'admission_failed' THEN
    SELECT count(*) INTO terminal_event_count
    FROM agent_event_outbox WHERE agent_run_id = NEW.agent_run_id;
    SELECT count(*) INTO usage_count
    FROM agent_run_usage WHERE agent_run_id = NEW.agent_run_id;
    SELECT count(*) INTO lease_count
    FROM agent_run_lease WHERE agent_run_id = NEW.agent_run_id;
    SELECT count(*) INTO manifest_count
    FROM agent_execution_manifest WHERE agent_run_id = NEW.agent_run_id;
    IF NEW.terminal_at IS DISTINCT FROM transaction_timestamp()
      OR NEW.execution_manifest_id IS NOT NULL
      OR NEW.terminal_claim_id IS NOT NULL
      OR NEW.next_event_seq <> 1
      OR NEW.usage_input_tokens <> 0
      OR NEW.usage_output_tokens <> 0
      OR NEW.usage_cached_tokens <> 0
      OR NEW.usage_call_count <> 0
      OR NEW.budget_tokens_used <> 0
      OR terminal_event_count <> 0
      OR usage_count <> 0
      OR lease_count <> 0
      OR manifest_count <> 0
    THEN
      RAISE EXCEPTION 'admission failure cannot create runtime evidence'
        USING ERRCODE='23514', CONSTRAINT='agent_run_admission_failure_boundary_ck';
    END IF;
  ELSIF NEW.terminal_at IS NOT NULL THEN
    RAISE EXCEPTION 'preterminal run cannot have a terminal timestamp'
      USING ERRCODE='23514', CONSTRAINT='agent_run_terminal_at_state_ck';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_run_terminal_completion_trigger
AFTER INSERT OR UPDATE OF state, terminal_at, next_event_seq,
  terminal_claim_id, terminal_claim_epoch, terminal_claim_lease_generation
ON agent_run
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_terminal_run_completion();

CREATE FUNCTION agent_reject_terminal_run_lease_mutation()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE run_state text;
DECLARE run_id uuid;
BEGIN
  run_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.agent_run_id ELSE NEW.agent_run_id END;
  SELECT state INTO run_state
  FROM agent_run WHERE agent_run_id = run_id FOR SHARE;
  IF run_state IN ('completed','failed','cancelled','admission_failed') THEN
    RAISE EXCEPTION 'terminal run lease evidence cannot be created, changed, or deleted'
      USING ERRCODE='23514', CONSTRAINT='agent_run_lease_terminal_run_ck';
  END IF;
  IF TG_OP = 'UPDATE' AND NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id THEN
    RAISE EXCEPTION 'run lease identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_run_lease_identity_immutable_ck';
  END IF;
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_run_lease_terminal_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_run_lease
FOR EACH ROW EXECUTE FUNCTION agent_reject_terminal_run_lease_mutation();

CREATE FUNCTION agent_reject_manifest_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE run_state text;
BEGIN
  IF TG_OP = 'INSERT' THEN
    SELECT state INTO run_state
    FROM agent_run WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
    IF run_state IN ('completed','failed','cancelled','admission_failed') THEN
      RAISE EXCEPTION 'terminal agent run cannot gain an execution manifest'
        USING ERRCODE='23514', CONSTRAINT='agent_execution_manifest_terminal_run_ck';
    END IF;
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'execution manifest is immutable'
    USING ERRCODE='23514', CONSTRAINT='agent_execution_manifest_immutable_ck';
END;
$$;

CREATE TRIGGER agent_execution_manifest_immutable_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_execution_manifest
FOR EACH ROW EXECUTE FUNCTION agent_reject_manifest_update();

CREATE FUNCTION agent_validate_event_epoch()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE current_epoch bigint;
DECLARE current_next_event_seq bigint;
DECLARE current_state text;
DECLARE current_terminal_claim_epoch bigint;
BEGIN
  SELECT epoch, next_event_seq, state, terminal_claim_epoch
  INTO current_epoch, current_next_event_seq, current_state, current_terminal_claim_epoch
  FROM agent_run
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
  IF NEW.kind IN ('run.completed','run.failed')
    AND current_terminal_claim_epoch IS DISTINCT FROM current_epoch
  THEN
    RAISE EXCEPTION 'terminal event requires the current terminal reservation'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_terminal_claim_ck';
  END IF;
  IF NEW.stream_index IS NULL AND (
    NEW.kind NOT IN ('run.completed','run.failed')
    OR NOT EXISTS (
      SELECT 1 FROM agent_projection_ack
      WHERE agent_run_id = NEW.agent_run_id AND consumer = 'chat'
        AND rejected_seq = NEW.seq - 1
    )
  ) THEN
    RAISE EXCEPTION 'only post-NACK terminal evidence may omit Redis wire metadata'
      USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_stream_metadata_required_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_event_outbox_current_epoch_trigger
BEFORE INSERT ON agent_event_outbox
FOR EACH ROW EXECUTE FUNCTION agent_validate_event_epoch();

CREATE FUNCTION agent_validate_terminal_event_completion()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE run_state text;
DECLARE run_terminal_at timestamptz;
BEGIN
  IF NEW.kind IN ('run.completed','run.failed') THEN
    SELECT state, terminal_at INTO run_state, run_terminal_at
    FROM agent_run WHERE agent_run_id = NEW.agent_run_id;
    IF NEW.kind IS DISTINCT FROM (CASE
        WHEN run_state IN ('completed','cancelled') THEN 'run.completed'
        WHEN run_state = 'failed' THEN 'run.failed'
        ELSE NULL
      END)
      OR run_terminal_at IS DISTINCT FROM NEW.created_at
    THEN
      RAISE EXCEPTION 'terminal event and run state must finalize in one transaction'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_terminal_complete_ck';
    END IF;
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_event_outbox_terminal_complete_trigger
AFTER INSERT ON agent_event_outbox
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_terminal_event_completion();

CREATE FUNCTION agent_validate_event_evidence_mutation()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE safe_watermark bigint;
DECLARE rejection_fence bigint;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.published_at IS NOT NULL OR NEW.acked_at IS NOT NULL
      OR NEW.last_publish_attempt_at IS NOT NULL OR NEW.publish_attempt <> 0
    THEN
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
    OR NEW.stream_index IS DISTINCT FROM OLD.stream_index
    OR NEW.stream_timestamp_ms IS DISTINCT FROM OLD.stream_timestamp_ms
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
  IF OLD.published_at IS NULL AND NEW.published_at IS NOT NULL THEN
    IF NEW.stream_index IS NULL THEN
      RAISE EXCEPTION 'internal terminal evidence has no publishable Redis wire metadata'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_internal_evidence_publish_ck';
    END IF;
    SELECT rejected_seq INTO rejection_fence
    FROM agent_projection_ack
    WHERE agent_run_id = NEW.agent_run_id AND consumer = 'chat'
    FOR SHARE;
    IF rejection_fence IS NOT NULL AND NEW.seq > rejection_fence THEN
      RAISE EXCEPTION 'event publication is fenced after the first projection rejection'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_rejection_publish_fence_ck';
    END IF;
    IF NEW.published_at IS DISTINCT FROM transaction_timestamp()
      OR NEW.last_publish_attempt_at IS DISTINCT FROM transaction_timestamp()
      OR NEW.publish_attempt <> 1
      OR OLD.last_publish_attempt_at IS NOT NULL
      OR OLD.publish_attempt <> 0
    THEN
      RAISE EXCEPTION 'first publication must record its first transaction-bound attempt'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_publish_attempt_ck';
    END IF;
  ELSIF NEW.last_publish_attempt_at IS DISTINCT FROM OLD.last_publish_attempt_at
    OR NEW.publish_attempt IS DISTINCT FROM OLD.publish_attempt
  THEN
    IF OLD.published_at IS NULL
      OR NEW.published_at IS DISTINCT FROM OLD.published_at
      OR OLD.acked_at IS NOT NULL OR NEW.acked_at IS NOT NULL
      OR NEW.last_publish_attempt_at IS DISTINCT FROM transaction_timestamp()
      OR NEW.last_publish_attempt_at < OLD.last_publish_attempt_at
      OR NEW.publish_attempt <> OLD.publish_attempt + 1
    THEN
      RAISE EXCEPTION 'event republish attempt must advance once while unacknowledged'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_republish_attempt_ck';
    END IF;
    SELECT rejected_seq INTO rejection_fence
    FROM agent_projection_ack
    WHERE agent_run_id = NEW.agent_run_id AND consumer = 'chat'
    FOR SHARE;
    IF rejection_fence IS NOT NULL AND NEW.seq >= rejection_fence THEN
      RAISE EXCEPTION 'event republish is fenced after the first projection rejection'
        USING ERRCODE='23514', CONSTRAINT='agent_event_outbox_rejection_publish_fence_ck';
    END IF;
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE current_epoch bigint;
DECLARE current_next_event_seq bigint;
DECLARE is_first_rejection boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'projection acknowledgement and first rejection evidence cannot be deleted'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_delete_ck';
  END IF;
  IF TG_OP = 'INSERT' THEN
    is_first_rejection := NEW.rejected_seq IS NOT NULL;
    IF NEW.generation <> 1 THEN
      RAISE EXCEPTION 'projection acknowledgement must start at generation one'
        USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_initial_generation_ck';
    END IF;
  ELSE
    is_first_rejection := NEW.rejected_seq IS NOT NULL AND OLD.rejected_seq IS NULL;
  END IF;
  SELECT epoch, next_event_seq
  INTO current_epoch, current_next_event_seq
  FROM agent_run
  WHERE agent_run_id = NEW.agent_run_id
  FOR SHARE;
  IF current_epoch IS NULL
    OR NEW.projected_epoch > current_epoch
    OR NEW.projected_seq > current_next_event_seq - 1
  THEN
    RAISE EXCEPTION 'projection acknowledgement is outside the current run fence'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_current_fence_ck';
  END IF;
  IF TG_OP = 'UPDATE'
    AND NEW.projected_seq = 0
    AND (NEW.projected_epoch IS DISTINCT FROM OLD.projected_epoch
      OR NEW.projected_seq IS DISTINCT FROM OLD.projected_seq)
  THEN
    RAISE EXCEPTION 'zero projection watermark cannot be relabelled to another epoch'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_zero_epoch_immutable_ck';
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
  IF TG_OP = 'UPDATE' THEN
    IF NEW.generation <> OLD.generation + 1 THEN
      RAISE EXCEPTION 'projection mutation requires the next CAS generation'
        USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_generation_cas_ck';
    END IF;
    IF NEW.projected_epoch IS NOT DISTINCT FROM OLD.projected_epoch
      AND NEW.projected_seq IS NOT DISTINCT FROM OLD.projected_seq
      AND NEW.producer_close_requested IS NOT DISTINCT FROM OLD.producer_close_requested
      AND NEW.consumer_closed IS NOT DISTINCT FROM OLD.consumer_closed
      AND NEW.rejected_seq IS NOT DISTINCT FROM OLD.rejected_seq
      AND NEW.rejection_code IS NOT DISTINCT FROM OLD.rejection_code
      AND NEW.rejected_at IS NOT DISTINCT FROM OLD.rejected_at
    THEN
      RAISE EXCEPTION 'projection generation cannot advance without a durable direction'
        USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_noop_generation_ck';
    END IF;
    NEW.updated_at := transaction_timestamp();
    IF OLD.producer_close_requested AND NOT NEW.producer_close_requested
      OR OLD.consumer_closed AND NOT NEW.consumer_closed
    THEN
      RAISE EXCEPTION 'projection close state is one-way'
        USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_close_monotonic_ck';
    END IF;
    IF OLD.rejected_seq IS NOT NULL AND (
      NEW.rejected_seq IS DISTINCT FROM OLD.rejected_seq
      OR NEW.rejection_code IS DISTINCT FROM OLD.rejection_code
      OR NEW.rejected_at IS DISTINCT FROM OLD.rejected_at
      OR NEW.projected_epoch IS DISTINCT FROM OLD.projected_epoch
      OR NEW.projected_seq IS DISTINCT FROM OLD.projected_seq
    ) THEN
      RAISE EXCEPTION 'first projection rejection is immutable and stops positive ack'
        USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_rejection_one_way_ck';
    END IF;
  END IF;

  IF is_first_rejection THEN
    IF NEW.rejected_seq <> NEW.projected_seq + 1
      OR NEW.rejected_at IS DISTINCT FROM transaction_timestamp()
      OR (TG_OP = 'UPDATE' AND (
        NEW.projected_epoch IS DISTINCT FROM OLD.projected_epoch
        OR NEW.projected_seq IS DISTINCT FROM OLD.projected_seq
      ))
      OR NOT EXISTS (
        SELECT 1 FROM agent_event_outbox
        WHERE agent_run_id = NEW.agent_run_id
          AND seq = NEW.rejected_seq
          AND published_at IS NOT NULL
      )
      OR EXISTS (
        SELECT 1 FROM agent_event_outbox
        WHERE agent_run_id = NEW.agent_run_id
          AND seq > NEW.rejected_seq
          AND published_at IS NOT NULL
      )
    THEN
      RAISE EXCEPTION 'projection rejection must fence the first current published event'
        USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_rejection_fence_ck';
    END IF;
  END IF;
  IF TG_OP = 'UPDATE'
    AND OLD.rejected_seq IS NULL
    AND NEW.rejected_seq IS NULL
    AND (NEW.projected_epoch IS DISTINCT FROM OLD.projected_epoch
      OR NEW.projected_seq IS DISTINCT FROM OLD.projected_seq)
    AND (NEW.producer_close_requested IS DISTINCT FROM OLD.producer_close_requested
      OR NEW.consumer_closed IS DISTINCT FROM OLD.consumer_closed)
  THEN
    RAISE EXCEPTION 'positive ack and close mutation must use separate CAS steps'
      USING ERRCODE='23514', CONSTRAINT='agent_projection_ack_single_direction_ck';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_projection_ack_monotonic_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_projection_ack
FOR EACH ROW EXECUTE FUNCTION agent_reject_projection_ack_regression();

CREATE FUNCTION agent_validate_tool_effect_transition()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE run_state text;
DECLARE run_epoch bigint;
DECLARE lease_generation bigint;
DECLARE lease_deadline timestamptz;
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.effect_kind <> 'tool_journal' OR OLD.status <> 'claimed' THEN
      RAISE EXCEPTION 'terminal or external tool effect evidence cannot be deleted'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_immutable_ck';
    END IF;
    SELECT state, epoch INTO run_state, run_epoch
    FROM agent_run WHERE agent_run_id = OLD.agent_run_id FOR SHARE;
    SELECT generation, leased_until INTO lease_generation, lease_deadline
    FROM agent_run_lease WHERE agent_run_id = OLD.agent_run_id FOR SHARE;
    IF run_state IN ('completed','failed','cancelled','admission_failed')
      OR lease_generation IS NULL
      OR lease_deadline <= transaction_timestamp()
      OR OLD.claim_epoch IS DISTINCT FROM run_epoch
      OR OLD.claim_lease_generation IS DISTINCT FROM lease_generation
    THEN
      RAISE EXCEPTION 'tool journal clear requires the current live run lease fence'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_journal_clear_fence_ck';
    END IF;
    RETURN OLD;
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'claimed' OR NEW.result_digest IS NOT NULL
      OR NEW.result_schema_version IS NOT NULL OR NEW.result_payload IS NOT NULL
      OR NEW.result_is_error IS NOT NULL
    THEN
      RAISE EXCEPTION 'tool effect must be claimed before an external effect'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_claim_first_ck';
    END IF;
    SELECT state, epoch INTO run_state, run_epoch
    FROM agent_run
    WHERE agent_run_id = NEW.agent_run_id
    FOR SHARE;
    IF run_state IN ('completed','failed','cancelled','admission_failed') THEN
      RAISE EXCEPTION 'terminal agent run cannot claim a new tool effect'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_terminal_run_ck';
    END IF;
    SELECT generation, leased_until INTO lease_generation, lease_deadline
    FROM agent_run_lease WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
    IF NEW.claim_epoch <> run_epoch
      OR NEW.claim_lease_generation IS DISTINCT FROM lease_generation
      OR lease_deadline <= transaction_timestamp()
    THEN
      RAISE EXCEPTION 'tool effect claim fence must match the current live lease'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_claim_fence_ck';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.effect_id IS DISTINCT FROM OLD.effect_id
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.tool_call_id IS DISTINCT FROM OLD.tool_call_id
    OR NEW.tool_name IS DISTINCT FROM OLD.tool_name
    OR NEW.effect_kind IS DISTINCT FROM OLD.effect_kind
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
    OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION 'tool effect claim identity is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_claim_immutable_ck';
  END IF;
  SELECT state, epoch INTO run_state, run_epoch
  FROM agent_run WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
  SELECT generation, leased_until INTO lease_generation, lease_deadline
  FROM agent_run_lease WHERE agent_run_id = NEW.agent_run_id FOR SHARE;
  IF run_state IN ('completed','failed','cancelled','admission_failed')
    AND OLD.status NOT IN ('completed','failed')
  THEN
    RAISE EXCEPTION 'terminal run cannot finalize an outstanding tool effect'
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_terminal_run_ck';
  END IF;
  IF NEW.claim_epoch IS DISTINCT FROM OLD.claim_epoch
    OR NEW.claim_lease_generation IS DISTINCT FROM OLD.claim_lease_generation
  THEN
    IF OLD.status <> 'unknown' OR NEW.status <> 'unknown'
      OR NEW.claim_epoch <> run_epoch
      OR NEW.claim_lease_generation IS DISTINCT FROM lease_generation
      OR lease_deadline <= transaction_timestamp()
    THEN
      RAISE EXCEPTION 'only unknown tool effects may be explicitly adopted by the current lease'
        USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_unknown_adoption_ck';
    END IF;
  ELSIF OLD.claim_epoch <> run_epoch
    OR OLD.claim_lease_generation IS DISTINCT FROM lease_generation
    OR lease_deadline <= transaction_timestamp()
  THEN
    RAISE EXCEPTION 'stale tool effect claimant cannot mutate effect state'
      USING ERRCODE='23514', CONSTRAINT='agent_tool_effect_claim_fence_ck';
  END IF;
  IF OLD.status IN ('completed','failed') AND (
    NEW.status IS DISTINCT FROM OLD.status
    OR NEW.result_digest IS DISTINCT FROM OLD.result_digest
    OR NEW.result_schema_version IS DISTINCT FROM OLD.result_schema_version
    OR NEW.result_payload IS DISTINCT FROM OLD.result_payload
    OR NEW.result_is_error IS DISTINCT FROM OLD.result_is_error
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
DECLARE run_state text;
DECLARE run_terminal_at timestamptz;
DECLARE run_input bigint;
DECLARE run_output bigint;
DECLARE run_cached bigint;
DECLARE run_calls bigint;
DECLARE manifest_id uuid;
DECLARE manifest_model_revision_id uuid;
DECLARE manifest_feature_key text;
DECLARE matching_line_count integer;
DECLARE total_line_count integer;
BEGIN
  SELECT state, terminal_at, usage_input_tokens, usage_output_tokens,
    usage_cached_tokens, usage_call_count, execution_manifest_id
  INTO run_state, run_terminal_at, run_input, run_output, run_cached, run_calls,
    manifest_id
  FROM agent_run
  WHERE agent_run_id = NEW.agent_run_id
  FOR SHARE;
  IF run_state NOT IN ('completed','failed','cancelled') THEN
    RAISE EXCEPTION 'run usage can only be finalized for a terminal run'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_terminal_run_ck';
  END IF;
  IF NEW.finalized_at IS DISTINCT FROM transaction_timestamp()
    OR run_terminal_at IS DISTINCT FROM NEW.finalized_at
  THEN
    RAISE EXCEPTION 'run usage must be finalized in its creation transaction'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_finalization_time_ck';
  END IF;
  IF (NEW.input_tokens, NEW.output_tokens, NEW.cached_tokens, NEW.call_count)
    IS DISTINCT FROM (run_input, run_output, run_cached, run_calls)
  THEN
    RAISE EXCEPTION 'final usage must exactly match the durable accumulator'
      USING ERRCODE='23514', CONSTRAINT='agent_run_usage_accumulator_match_ck';
  END IF;

  SELECT count(*) INTO total_line_count
  FROM agent_run_usage_line WHERE run_usage_id = NEW.run_usage_id;
  IF manifest_id IS NULL THEN
    IF total_line_count <> 0
      OR (run_input, run_output, run_cached, run_calls)
        IS DISTINCT FROM (0::bigint,0::bigint,0::bigint,0::bigint)
    THEN
      RAISE EXCEPTION 'run without a manifest can finalize only zero aggregate usage'
        USING ERRCODE='23514', CONSTRAINT='agent_run_usage_manifest_match_ck';
    END IF;
  ELSE
    SELECT model_revision_id, usage_feature_key
    INTO manifest_model_revision_id, manifest_feature_key
    FROM agent_execution_manifest
    WHERE execution_manifest_id = manifest_id;
    SELECT count(*) INTO matching_line_count
    FROM agent_run_usage_line
    WHERE run_usage_id = NEW.run_usage_id
      AND model_revision_id = manifest_model_revision_id
      AND feature_key = manifest_feature_key
      AND (input_tokens, output_tokens, cached_tokens, call_count)
        IS NOT DISTINCT FROM (run_input, run_output, run_cached, run_calls);
    IF total_line_count <> 1 OR matching_line_count <> 1 THEN
      RAISE EXCEPTION 'usage lines must exactly match the manifest model and feature'
        USING ERRCODE='23514', CONSTRAINT='agent_run_usage_manifest_match_ck';
    END IF;
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER agent_run_usage_terminal_trigger
AFTER INSERT ON agent_run_usage
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION agent_validate_terminal_run_usage();

CREATE FUNCTION agent_reject_run_usage_mutation()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  RAISE EXCEPTION 'finalized run usage is immutable'
    USING ERRCODE='23514', CONSTRAINT='agent_run_usage_immutable_ck';
END;
$$;

CREATE TRIGGER agent_run_usage_immutable_trigger
BEFORE UPDATE OR DELETE ON agent_run_usage
FOR EACH ROW EXECUTE FUNCTION agent_reject_run_usage_mutation();

CREATE FUNCTION agent_validate_run_usage_line_mutation()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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

CREATE FUNCTION agent_validate_dispatch_dlq_transition()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'dispatch DLQ evidence cannot be deleted'
      USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_immutable_ck';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.retry_status <> 'pending' OR NEW.claim_generation <> 1
      OR NEW.claimed_by IS NOT NULL OR NEW.claimed_at IS NOT NULL
      OR NEW.claim_expires_at IS NOT NULL OR NEW.resolved_at IS NOT NULL
    THEN
      RAISE EXCEPTION 'dispatch DLQ evidence must start pending at generation one'
        USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_initial_state_ck';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.dlq_id IS DISTINCT FROM OLD.dlq_id
    OR NEW.agent_run_id IS DISTINCT FROM OLD.agent_run_id
    OR NEW.source_key IS DISTINCT FROM OLD.source_key
    OR NEW.raw_hash IS DISTINCT FROM OLD.raw_hash
    OR NEW.request_digest IS DISTINCT FROM OLD.request_digest
    OR NEW.error_code IS DISTINCT FROM OLD.error_code
    OR NEW.payload IS DISTINCT FROM OLD.payload
    OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION 'dispatch DLQ source and raw evidence are immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_evidence_immutable_ck';
  END IF;
  IF NEW IS NOT DISTINCT FROM OLD THEN
    RETURN NEW;
  END IF;
  IF OLD.retry_status IN ('resolved','abandoned') THEN
    RAISE EXCEPTION 'terminal dispatch DLQ resolution is immutable'
      USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_terminal_immutable_ck';
  END IF;
  NEW.updated_at := transaction_timestamp();
  IF NEW.claim_generation <> OLD.claim_generation + 1 THEN
    RAISE EXCEPTION 'dispatch DLQ mutation requires the next CAS generation'
      USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_generation_cas_ck';
  END IF;
  IF OLD.retry_status = 'pending' THEN
    IF NEW.retry_status <> 'retrying'
      OR NEW.claimed_at IS DISTINCT FROM transaction_timestamp()
      OR NEW.claim_expires_at <= transaction_timestamp()
      OR NEW.resolved_at IS NOT NULL
    THEN
      RAISE EXCEPTION 'dispatch DLQ must be claimed before repair'
        USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_transition_ck';
    END IF;
  ELSIF OLD.retry_status = 'retrying' THEN
    IF NEW.retry_status = 'retrying' THEN
      IF OLD.claim_expires_at > transaction_timestamp()
        OR NEW.claimed_at IS DISTINCT FROM transaction_timestamp()
        OR NEW.claim_expires_at <= transaction_timestamp()
        OR NEW.resolved_at IS NOT NULL
      THEN
        RAISE EXCEPTION 'live dispatch DLQ claim cannot be reclaimed'
          USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_reclaim_fence_ck';
      END IF;
    ELSIF NEW.retry_status IN ('resolved','abandoned') THEN
      IF OLD.claim_expires_at <= transaction_timestamp()
        OR NEW.claimed_by IS DISTINCT FROM OLD.claimed_by
        OR NEW.claimed_at IS DISTINCT FROM OLD.claimed_at
        OR NEW.claim_expires_at IS DISTINCT FROM OLD.claim_expires_at
        OR NEW.resolved_at IS DISTINCT FROM transaction_timestamp()
      THEN
        RAISE EXCEPTION 'dispatch DLQ repair must terminate with immutable claim evidence'
          USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_transition_ck';
      END IF;
    ELSE
      RAISE EXCEPTION 'invalid dispatch DLQ retry transition'
        USING ERRCODE='23514', CONSTRAINT='agent_dispatch_dlq_transition_ck';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER agent_dispatch_dlq_transition_trigger
BEFORE INSERT OR UPDATE OR DELETE ON agent_dispatch_dlq
FOR EACH ROW EXECUTE FUNCTION agent_validate_dispatch_dlq_transition();

CREATE FUNCTION agent_reject_control_claim_update()
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
-- sha256: 2adc248d3c3e2f79e5c23db0dbc0b345b99f64fc8695937a80efe6249cfbde42
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

-- source: database/schema/60-model.sql
-- sha256: bafda2bad1a2b334a1b30cd1ef408d4b19b518157e29099f1ad8ea382dd9e1b5
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
-- sha256: d6f62b5f62ce3d03ab9b928772ce0fc133d59cbada136fbd60dba89f20761902
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
RETURNS trigger LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, kokoro, pg_temp
AS $$
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
