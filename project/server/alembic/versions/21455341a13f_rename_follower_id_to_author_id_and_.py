"""Rename follower_id to author_id and followed_id to follower_id

Revision ID: 21455341a13f
Revises: dbbef938a8ff
Create Date: 2025-01-13 13:13:36.041357

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "21455341a13f"
down_revision: Union[str, None] = "dbbef938a8ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Переименование столбцов
    op.alter_column("followers", "follower_id", new_column_name="author_id")
    op.alter_column("followers", "followed_id", new_column_name="follower_id")


def downgrade() -> None:
    # Откат изменений
    op.alter_column("followers", "author_id", new_column_name="follower_id")
    op.alter_column("followers", "follower_id", new_column_name="followed_id")
