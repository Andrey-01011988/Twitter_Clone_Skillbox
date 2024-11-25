"""Alter timestamp column in tweets

Revision ID: 28424322dda2
Revises: 34043bb9f5c3
Create Date: 2024-11-25 13:12:50.684366

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = '28424322dda2'
down_revision: Union[str, None] = '34043bb9f5c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Изменяем колонку timestamp
    op.alter_column(
        'tweets',  # имя таблицы
        'timestamp',  # имя колонки
        existing_type=sa.DateTime(timezone=True),  # существующий тип
        type_=sa.DateTime(timezone=True),  # новый тип
        server_default=func.now(),  # новое значение по умолчанию
        existing_server_default=None,  # старое значение по умолчанию (если есть)
        nullable=False,  # можно сделать nullable=True, если нужно
    )


def downgrade() -> None:
    # Возвращаем изменения назад
    # op.alter_column(
    #     'tweets',
    #     'timestamp',
    #     existing_type=sa.DateTime(timezone=True),
    #     type_=sa.DateTime(),  # Предположим, что старый тип был без timezone
    #     server_default=datetime.now(timezone.utc),  # Удаляем значение по умолчанию
    #     existing_server_default=func.now(),  # Указываем на старое значение по умолчанию (если было)
    #     nullable=False,
    # )
    op.alter_column(
        'tweets',
        'timestamp',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),  # Предположим, что старый тип был без timezone
        server_default=None,  # Удаляем значение по умолчанию
        existing_server_default=func.now(),  # Указываем на старое значение по умолчанию (если было)
        nullable=False,
    )
