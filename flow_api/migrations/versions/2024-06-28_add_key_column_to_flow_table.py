"""Add key column to Flow table

Revision ID: 529277b5c3e7
Revises: 288bb3239e41
Create Date: 2024-06-28 17:46:24.205072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '529277b5c3e7'
down_revision: Union[str, None] = '288bb3239e41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the new `key` column with a temporary nullable setting
    op.add_column('flow', sa.Column('key', sa.String(length=200), nullable=True))

    # Move existing `name` values to `key`
    op.execute('UPDATE flow SET key = name')

    # Set the `key` column to be not nullable
    op.alter_column('flow', 'key', nullable=False)


def downgrade():
    op.drop_column('flow', 'key')
