"""Add analyst assignment and immutable application lifecycle history."""

import sqlalchemy as sa
from alembic import op

revision = "0002_application_lifecycle"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("credit_cases")}
    if "assigned_analyst" not in columns:
        op.add_column(
            "credit_cases",
            sa.Column("assigned_analyst", sa.String(length=255), nullable=True),
        )
        op.create_index(
            "ix_credit_cases_assigned_analyst",
            "credit_cases",
            ["assigned_analyst"],
        )
    if "case_history" not in inspector.get_table_names():
        op.create_table(
            "case_history",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("tenant_id", sa.Uuid(), nullable=False),
            sa.Column("case_id", sa.Uuid(), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("actor_id", sa.String(length=255), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("case_version", sa.Integer(), nullable=False),
            sa.Column("changes", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["case_id"], ["credit_cases.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("case_id", "sequence"),
        )
        op.create_index("ix_case_history_tenant_id", "case_history", ["tenant_id"])
        op.create_index("ix_case_history_case_id", "case_history", ["case_id"])
        op.create_index("ix_case_history_event_type", "case_history", ["event_type"])
        op.create_index("ix_case_history_occurred_at", "case_history", ["occurred_at"])
    op.execute("ALTER TABLE case_history ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY case_history_tenant_isolation ON case_history "
        "USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) "
        "WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)"
    )


def downgrade() -> None:
    op.drop_table("case_history")
    op.drop_index("ix_credit_cases_assigned_analyst", table_name="credit_cases")
    op.drop_column("credit_cases", "assigned_analyst")
