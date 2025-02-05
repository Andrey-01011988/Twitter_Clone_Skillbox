"""Update Media model

Revision ID: 9f19377a211e
Revises: 34043bb9f5c3
Create Date: 2024-12-02 10:43:35.896928

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9f19377a211e"
down_revision: Union[str, None] = "34043bb9f5c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("media", sa.Column("file_body", sa.LargeBinary(), nullable=False))
    op.add_column("media", sa.Column("file_name", sa.String(), nullable=False))
    op.alter_column("media", "tweet_id", existing_type=sa.INTEGER(), nullable=True)
    op.drop_column("media", "url")
    op.alter_column(
        "tweets",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "tweets",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
    )
    op.add_column(
        "media", sa.Column("url", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.alter_column("media", "tweet_id", existing_type=sa.INTEGER(), nullable=False)
    op.drop_column("media", "file_name")
    op.drop_column("media", "file_body")
    # ### end Alembic commands ###
