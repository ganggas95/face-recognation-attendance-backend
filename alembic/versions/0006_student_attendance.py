import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_student_attendance"
down_revision = "0005_school_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_attendance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "checkin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gate_attendances.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "checkout_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gate_attendances.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.UniqueConstraint(
            "student_id",
            "date",
            name="uq_student_attendance_student_date",
        ),
    )
    op.create_index(
        "ix_student_attendance_date",
        "student_attendance",
        ["date"],
        unique=False,
    )
    op.create_index(
        "ix_student_attendance_student_id",
        "student_attendance",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_student_attendance_status",
        "student_attendance",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_student_attendance_verified",
        "student_attendance",
        ["verified"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_attendance_verified",
        table_name="student_attendance",
    )
    op.drop_index(
        "ix_student_attendance_status",
        table_name="student_attendance",
    )
    op.drop_index(
        "ix_student_attendance_student_id",
        table_name="student_attendance",
    )
    op.drop_index(
        "ix_student_attendance_date",
        table_name="student_attendance",
    )
    op.drop_table("student_attendance")
