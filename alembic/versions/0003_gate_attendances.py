import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_gate_attendances"
down_revision = "0002_class_subject_assignments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gate_attendances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "recorded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "student_id",
            "date",
            "direction",
            name="uq_gate_attendance_student_date_direction",
        ),
    )
    op.create_index(
        "ix_gate_attendances_date",
        "gate_attendances",
        ["date"],
        unique=False,
    )
    op.create_index(
        "ix_gate_attendances_direction",
        "gate_attendances",
        ["direction"],
        unique=False,
    )
    op.create_index(
        "ix_gate_attendances_student_id",
        "gate_attendances",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_gate_attendances_recorded_by_user_id",
        "gate_attendances",
        ["recorded_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_gate_attendances_recorded_by_user_id",
        table_name="gate_attendances",
    )
    op.drop_index(
        "ix_gate_attendances_student_id",
        table_name="gate_attendances",
    )
    op.drop_index(
        "ix_gate_attendances_direction",
        table_name="gate_attendances",
    )
    op.drop_index(
        "ix_gate_attendances_date",
        table_name="gate_attendances",
    )
    op.drop_table("gate_attendances")

