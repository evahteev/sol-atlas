"""add discord user id

Revision ID: faef2b8b6d98
Revises: 480231aedfb3
Create Date: 2024-10-01 22:12:31.837930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faef2b8b6d98'
down_revision: Union[str, None] = '480231aedfb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("discord_user_id", sa.String(length=200), nullable=True, server_default=""),
    )

def downgrade() -> None:
    op.drop_column("user", "discord_user_id")

