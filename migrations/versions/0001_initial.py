"""Initial normalized schema, pgvector, FTS, and tenant RLS."""

from alembic import op

from creditflow.db.base import Base
from creditflow.db.models import entities  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=op.get_bind())
    # ORM-owned relational tables are emitted from the checked-in SQL to keep this migration reviewable.
    op.execute("""
    CREATE TABLE IF NOT EXISTS embedding_models (
      id uuid PRIMARY KEY, provider text NOT NULL, model text NOT NULL,
      version text NOT NULL, dimensions integer NOT NULL CHECK (dimensions > 0),
      active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(provider, model, version)
    );
    CREATE TABLE IF NOT EXISTS document_chunk_embeddings (
      tenant_id uuid NOT NULL, chunk_id uuid NOT NULL,
      embedding_model_id uuid NOT NULL REFERENCES embedding_models(id),
      embedding vector(1536) NOT NULL,
      PRIMARY KEY (chunk_id, embedding_model_id)
    );
    CREATE INDEX IF NOT EXISTS ix_chunk_embedding_hnsw ON document_chunk_embeddings
      USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
    """)
    # Dimension changes create a new dimension-specific table/index and model row; never alter in place.
    op.execute("""
    ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS search_vector tsvector
      GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;
    CREATE INDEX IF NOT EXISTS ix_document_chunks_fts ON document_chunks USING gin(search_vector);
    CREATE INDEX IF NOT EXISTS ix_policy_effective_filter ON policy_documents
      (tenant_id, jurisdiction, category, effective_date, expiration_date);
    """)
    tenant_tables = [
        "users",
        "user_roles",
        "borrowers",
        "credit_cases",
        "documents",
        "document_versions",
        "document_chunks",
        "financial_facts",
        "financial_metrics",
        "credit_analyses",
        "risk_findings",
        "compliance_findings",
        "policy_documents",
        "workflow_runs",
        "workflow_checkpoints",
        "background_jobs",
        "human_reviews",
        "audit_events",
        "model_usage_events",
    ]
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid)"
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunk_embeddings")
    op.execute("DROP TABLE IF EXISTS embedding_models")
    Base.metadata.drop_all(bind=op.get_bind())
