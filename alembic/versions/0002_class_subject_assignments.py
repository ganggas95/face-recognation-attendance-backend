import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_class_subject_assignments"
down_revision = "0001_init_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("subjects", "teacher_id", nullable=True)

    op.create_table(
        "class_subject_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "class_instance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("class_instances.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subjects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "teacher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teachers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "class_instance_id",
            "subject_id",
            name="uq_class_subject_assignment",
        ),
    )
    op.create_index(
        "ix_class_subject_assignments_class_instance_id",
        "class_subject_assignments",
        ["class_instance_id"],
        unique=False,
    )
    op.create_index(
        "ix_class_subject_assignments_teacher_id",
        "class_subject_assignments",
        ["teacher_id"],
        unique=False,
    )
    op.create_index(
        "ix_class_subject_assignments_subject_id",
        "class_subject_assignments",
        ["subject_id"],
        unique=False,
    )

    op.add_column(
        "class_subject_schedules",
        sa.Column(
            "class_subject_assignment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_class_subject_schedules_assignment",
        "class_subject_schedules",
        "class_subject_assignments",
        ["class_subject_assignment_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_class_subject_schedules_class_subject_assignment_id",
        "class_subject_schedules",
        ["class_subject_assignment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_class_subject_schedules_class_subject_assignment_id",
        table_name="class_subject_schedules",
    )
    op.drop_constraint(
        "fk_class_subject_schedules_assignment",
        "class_subject_schedules",
        type_="foreignkey",
    )
    op.drop_column("class_subject_schedules", "class_subject_assignment_id")

    op.drop_index(
        "ix_class_subject_assignments_subject_id",
        table_name="class_subject_assignments",
    )
    op.drop_index(
        "ix_class_subject_assignments_teacher_id",
        table_name="class_subject_assignments",
    )
    op.drop_index(
        "ix_class_subject_assignments_class_instance_id",
        table_name="class_subject_assignments",
    )
    op.drop_table("class_subject_assignments")

    op.alter_column("subjects", "teacher_id", nullable=False)
