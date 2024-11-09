"""add chain_id column in invites

Revision ID: bd55fed1a414
Revises: 6a229d505bbb
Create Date: 2024-05-28 10:38:39.909480

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bd55fed1a414"
down_revision: Union[str, None] = "6a229d505bbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invite",
        sa.Column("wallet_address", sa.String(length=200), nullable=False),
    )
    op.add_column(
        "invite",
        sa.Column("token_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "invite",
        sa.Column("chain_id", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("invite", "token_id")
    op.drop_column("invite", "wallet_address")
    op.drop_column("invite", "chain_id")
