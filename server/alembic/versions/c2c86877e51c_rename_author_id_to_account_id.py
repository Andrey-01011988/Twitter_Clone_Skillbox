"""Rename author_id to account_id

Revision ID: c2c86877e51c
Revises: 21455341a13f
Create Date: 2025-01-13 13:43:40.209578

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2c86877e51c"
down_revision: Union[str, None] = "21455341a13f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Переименование столбцов
    op.alter_column("followers", "author_id", new_column_name="account_id")


def downgrade() -> None:
    # Откат изменений
    op.alter_column("followers", "account_id", new_column_name="author_id")
