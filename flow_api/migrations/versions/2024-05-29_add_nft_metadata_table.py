"""add nft metadata table

Revision ID: 6886e0fad606
Revises: bd55fed1a414
Create Date: 2024-05-29 13:40:56.873558

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6886e0fad606"
down_revision: Union[str, None] = "bd55fed1a414"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nft_metadata",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("token_id", sa.Integer(), nullable=False),
        sa.Column("art_id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["art_id"], ["art.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("nft_metadata")
