"""adding address and parent_id to collection

Revision ID: 2e32488e50e7
Revises: faef2b8b6d98
Create Date: 2024-10-22 18:53:04.601694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e32488e50e7'
down_revision: Union[str, None] = 'faef2b8b6d98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "artcollection",
        sa.Column("address", sa.String(length=200), nullable=True, server_default=""),
    )
    op.add_column(
        "artcollection",
        sa.Column('parent_id', sa.UUID(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("artcollection", "address")
    op.drop_column("artcollection", "parent_id")
