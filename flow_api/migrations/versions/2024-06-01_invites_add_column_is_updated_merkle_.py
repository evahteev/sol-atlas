"""invites add column is_updated_merkle_root

Revision ID: 90cbd5e7367b
Revises: 6886e0fad606
Create Date: 2024-06-01 00:54:42.979811

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "90cbd5e7367b"
down_revision: Union[str, None] = "6886e0fad606"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invite",
        sa.Column(
            "is_updated_merkle_root",
            sa.Boolean(),
            nullable=False,
            default=False,
            server_default="true",
        ),
    )


def downgrade() -> None:
    op.drop_column("invites", "is_updated_merkle_root")
