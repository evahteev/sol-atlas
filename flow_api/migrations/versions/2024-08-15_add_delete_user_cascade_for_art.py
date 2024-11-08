"""add delete user cascade for art

Revision ID: 97447595c87a
Revises: f40b7fe57394
Create Date: 2024-08-15 13:44:26.762480

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "97447595c87a"
down_revision: Union[str, None] = "f40b7fe57394"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("art_user_id_fkey", "art", type_="foreignkey")
    op.create_foreign_key(
        "art_user_id_fkey",
        "art",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("art_user_id_fkey", "art", type_="foreignkey")
    op.create_foreign_key(
        "art_user_id_fkey",
        "art",
        "user",
        ["user_id"],
        ["id"],
    )
