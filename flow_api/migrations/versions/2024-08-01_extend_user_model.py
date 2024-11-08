"""extend user model

Revision ID: b6c5cdc7f9f1
Revises: 9bfc8eeaa5da
Create Date: 2024-08-01 11:54:29.818534

"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6c5cdc7f9f1"
down_revision: Union[str, None] = "9bfc8eeaa5da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create Web3User table
    op.create_table(
        "web3_users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("wallet_address", sa.String(length=255), nullable=False),
        sa.Column("network_type", sa.String(length=50), nullable=False),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("private_key", sa.String(length=300), nullable=True, default=None),
    )

    # Create TelegramUser table
    op.create_table(
        "telegram_users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("telegram_id", sa.BIGINT, nullable=False),
        sa.Column("is_premium", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("telegram_users")
    op.drop_table("web3_users")
