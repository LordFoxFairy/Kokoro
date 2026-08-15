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
