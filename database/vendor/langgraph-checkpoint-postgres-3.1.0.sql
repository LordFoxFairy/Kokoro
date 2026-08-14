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
