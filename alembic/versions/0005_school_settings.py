import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_school_settings"
down_revision = "0004_student_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "school_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "key",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "gate_in_time",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'07:00:00'"),
        ),
        sa.Column(
            "gate_out_time",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'15:00:00'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("key", name="uq_school_settings_key"),
    )
    op.create_index(
        "ix_school_settings_key",
        "school_settings",
        ["key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_school_settings_key", table_name="school_settings")
    op.drop_table("school_settings")

