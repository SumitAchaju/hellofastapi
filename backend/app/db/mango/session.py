from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from app.core.settings import DATABASE


class MangoSessionManager:
    def __init__(self, host: str, dbname: str) -> None:
        self.client = AsyncIOMotorClient(host)
        self.engine = AIOEngine(client=self.client, database=dbname)

    async def close(self):
        if self.client is None:
            raise Exception("MangoSessionManager is not initialized")
        self.client.close()

        self.engine = None
        self.client = None


mango_sessionmanager = MangoSessionManager(DATABASE["MANGODB_URL"], "chatsystem")
