from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres.session import sessionmanager


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session


postgres_dependency = Annotated[AsyncSession, Depends(get_db_session)]
