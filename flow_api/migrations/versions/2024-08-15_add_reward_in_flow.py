"""add reward in flow

Revision ID: f40b7fe57394
Revises: b6c5cdc7f9f1
Create Date: 2024-08-15 11:18:55.239419

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f40b7fe57394"
down_revision: Union[str, None] = "b6c5cdc7f9f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "flow", sa.Column("reward", sa.Float(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    op.drop_column("flow", "reward")
