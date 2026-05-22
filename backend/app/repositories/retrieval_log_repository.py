from __future__ import annotations

from app.db.mongodb import get_database
from app.models.retrieval_log import RetrievalLogModel


class RetrievalLogRepository:
    collection_name = "retrieval_logs"

    def _collection(self):
        return get_database()[self.collection_name]

    async def create_log(self, log: RetrievalLogModel) -> str:
        await self._collection().insert_one(log.model_dump(by_alias=True))
        return log.id
