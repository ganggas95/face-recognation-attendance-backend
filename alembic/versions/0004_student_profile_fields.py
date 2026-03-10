import sqlalchemy as sa
from alembic import op

revision = "0004_student_profile_fields"
down_revision = "0003_gate_attendances"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("gender", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("birth_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("address", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("guardian_name", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("guardian_phone", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("students", "guardian_phone")
    op.drop_column("students", "guardian_name")
    op.drop_column("students", "address")
    op.drop_column("students", "birth_date")
    op.drop_column("students", "gender")
