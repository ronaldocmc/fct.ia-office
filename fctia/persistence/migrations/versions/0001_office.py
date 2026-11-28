"""Initial Office schema. Forward-only; destructive downgrade prohibited."""
from alembic import op
from pathlib import Path

revision = "0001_office"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Baseline SQL is immutable after release; transaction owned by Alembic.
    sql = (Path(__file__).resolve().parents[2] / "001_office.sql").read_text(encoding="utf-8")
    lines = [line for line in sql.splitlines()
             if not line.lstrip().startswith("--") and line.strip() not in ("BEGIN;", "COMMIT;")]
    for statement in "\n".join(lines).split(";"):
        if statement.strip():
            op.get_bind().exec_driver_sql(statement)

def downgrade():
    raise RuntimeError("Destructive downgrade disabled; restore verified backup instead")
