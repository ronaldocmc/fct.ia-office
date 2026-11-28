-- Baseline PostgreSQL 17, experimental synthetic data only.
-- Apply transactionally using a dedicated Office migration role, not Paperclip's role.
BEGIN;
CREATE SCHEMA IF NOT EXISTS office_runtime;
CREATE TABLE office_runtime.tasks (
 id uuid PRIMARY KEY,
 title text NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
 skill text NOT NULL,
 payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object' AND payload @> '{"synthetic":true}'::jsonb),
 state text NOT NULL CHECK (state IN ('created','assigned','running','failed','awaiting_review','approved','revision_requested')),
 agent text,
 result jsonb,
 review jsonb,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE office_runtime.events (
 seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 task_id uuid NOT NULL REFERENCES office_runtime.tasks(id) ON DELETE RESTRICT,
 actor text NOT NULL,
 action text NOT NULL,
 state text NOT NULL,
 occurred_at timestamptz NOT NULL,
 evidence jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX events_task_seq ON office_runtime.events(task_id,seq);
CREATE TABLE office_runtime.knowledge (
 id uuid PRIMARY KEY,
 scope text NOT NULL CHECK (length(trim(scope)) > 0),
 content text NOT NULL CHECK (length(trim(content)) > 0),
 source text NOT NULL CHECK (length(trim(source)) > 0),
 state text NOT NULL CHECK (state IN ('pending','approved')),
 created_at timestamptz NOT NULL,
 reviewer text,
 reviewed_at timestamptz,
 CHECK ((state='pending' AND reviewer IS NULL AND reviewed_at IS NULL)
     OR (state='approved' AND reviewer IS NOT NULL AND length(trim(reviewer)) > 0 AND reviewed_at IS NOT NULL))
);
CREATE INDEX knowledge_approved_scope ON office_runtime.knowledge(scope,created_at,id) WHERE state='approved';
REVOKE ALL ON SCHEMA office_runtime FROM PUBLIC;
COMMIT;
