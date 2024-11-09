"""add flows

Revision ID: b29fe2cb740c
Revises: 90cbd5e7367b
Create Date: 2024-06-04 14:32:29.786597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b29fe2cb740c'
down_revision: Union[str, None] = '90cbd5e7367b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "flow",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column('img_picture', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('reference_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('flow')
