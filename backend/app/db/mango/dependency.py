from typing import Annotated

from fastapi import Depends
from odmantic.session import AIOSession
from app.db.mango.session import mango_sessionmanager


async def get_mango_db():
    if mango_sessionmanager.engine is None:
        raise Exception("MangoSessionManager is not initialized")
    async with mango_sessionmanager.engine.session() as session:
        yield session


mangodb_dependency = Annotated[AIOSession, Depends(get_mango_db)]
