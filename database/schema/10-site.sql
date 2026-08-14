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
