"""Insert data into role and right

Revision ID: f9e96a712e7d
Revises: 1d7cba497094
Create Date: 2025-01-20 23:34:17.007963

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from alembic import op
import server.config as cgf
from server.models import Right, Role, roles_rights

# revision identifiers, used by Alembic.
revision: str = "f9e96a712e7d"
down_revision: Union[str, None] = "1d7cba497094"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


async def insert_data(async_conn: AsyncConnection):
    session = AsyncSession(bind=async_conn)
    try:
        for role in cgf.ROLE_RIGHTS_SCHEMA:
            role_obj = Role(name=role["name"])
            role_obj.rights.extend([Right(**right) for right in role["rights"]])
            session.add(role_obj)
        await session.commit()
    finally:
        await session.close()


async def delete_data(async_conn: AsyncConnection):
    session = AsyncSession(bind=async_conn)
    try:
        await session.execute(sa.delete(roles_rights))
        await session.execute(sa.delete(Role))
        await session.execute(sa.delete(Right))
        await session.commit()
    finally:
        await session.close()


def upgrade() -> None:
    op.run_async(insert_data)


def downgrade() -> None:
    op.run_async(delete_data)
