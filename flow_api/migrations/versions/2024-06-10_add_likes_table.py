"""add likes table

Revision ID: 288bb3239e41
Revises: b29fe2cb740c
Create Date: 2024-06-10 14:28:22.297618

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "288bb3239e41"
down_revision: Union[str, None] = "b29fe2cb740c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "art_likes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("art_id", sa.UUID),
        sa.Column("user_id", sa.UUID),
        sa.ForeignKeyConstraint(["art_id"], ["art.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("art_id", "user_id"),
    )


def downgrade():
    op.drop_table("art_likes")
