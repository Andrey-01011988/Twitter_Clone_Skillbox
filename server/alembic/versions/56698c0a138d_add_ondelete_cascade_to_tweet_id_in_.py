"""Add ondelete cascade to tweet_id in Like model

Revision ID: 56698c0a138d
Revises: c2c86877e51c
Create Date: 2025-01-14 12:02:47.221212

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "56698c0a138d"
down_revision: Union[str, None] = "c2c86877e51c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем старый внешний ключ
    op.drop_constraint("likes_tweet_id_fkey", "likes", type_="foreignkey")

    # Добавляем новый внешний ключ с ondelete='CASCADE'
    op.create_foreign_key(
        "likes_tweet_id_fkey",
        "likes",
        "tweets",
        ["tweet_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Удаляем новый внешний ключ
    op.drop_constraint("likes_tweet_id_fkey", "likes", type_="foreignkey")

    # Восстанавливаем старый внешний ключ без ondelete='CASCADE'
    op.create_foreign_key(
        "likes_tweet_id_fkey", "likes", "tweets", ["tweet_id"], ["id"]
    )
