"""Users, revocable sessions and classified music resources."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("login", sa.String(32), nullable=False, unique=True),
        sa.Column("email", sa.String(320)),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("clearance_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_music_account", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("clearance_level BETWEEN 1 AND 3"))
    op.create_table("sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False))
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])
    op.create_table("tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("artist", sa.String(200), nullable=False),
        sa.Column("security_level", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(255), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("security_level BETWEEN 1 AND 3"))


def downgrade():
    op.drop_table("tracks")
    op.drop_table("sessions")
    op.drop_table("users")
