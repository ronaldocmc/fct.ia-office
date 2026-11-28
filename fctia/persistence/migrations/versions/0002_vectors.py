"""Versioned embeddings for approved knowledge, with explicit model identity."""
from alembic import op

revision = "0002_vectors"
down_revision = "0001_office"
branch_labels = None
depends_on = None

def upgrade():
    # Extension must be provisioned by the database administrator in public.
    op.execute("""CREATE TABLE office_runtime.embeddings (
        knowledge_id uuid NOT NULL REFERENCES office_runtime.knowledge(id) ON DELETE RESTRICT,
        model text NOT NULL CHECK (length(trim(model)) > 0),
        content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
        embedding public.vector(384) NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (knowledge_id,model)
    )""")
    op.execute("CREATE INDEX embeddings_model ON office_runtime.embeddings(model)")

def downgrade():
    raise RuntimeError("Restore verified backup instead of destructive downgrade")
