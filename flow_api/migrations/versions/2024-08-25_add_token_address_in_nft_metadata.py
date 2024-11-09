"""add token address in nft_metadata

Revision ID: 480231aedfb3
Revises: 2b88eff30f43
Create Date: 2024-08-25 16:33:21.902517

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "480231aedfb3"
down_revision: Union[str, None] = "2b88eff30f43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "nft_metadata",
        sa.Column(
            "token_address", sa.String(length=200), nullable=True, server_default=""
        ),
    )


def downgrade() -> None:
    op.drop_column("nft_metadata", "token_address")
