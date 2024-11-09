"""extend art table with symbol

Revision ID: 2b88eff30f43
Revises: 97447595c87a
Create Date: 2024-08-25 14:16:15.204455

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2b88eff30f43"
down_revision: Union[str, None] = "97447595c87a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "art",
        sa.Column("symbol", sa.String(length=32), nullable=True, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("art", "symbol")
