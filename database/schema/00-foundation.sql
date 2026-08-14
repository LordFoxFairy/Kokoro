CREATE SCHEMA IF NOT EXISTS kokoro;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA kokoro;
ALTER ROLE CURRENT_USER SET search_path TO kokoro, pg_catalog;
SET search_path TO kokoro, pg_catalog;
