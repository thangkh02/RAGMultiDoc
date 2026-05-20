from datetime import datetime
from typing import Any, Optional

from app.db.mongodb import get_database
from app.models.session import SessionModel


class SessionRepository:
    collection_name = "sessions"

    def _collection(self):
        return get_database()[self.collection_name]

    async def create_session(self, session: SessionModel) -> str:
        await self._collection().insert_one(session.model_dump(by_alias=True))
        return session.id

    async def list_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        cursor = self._collection().find({"owner_user_id": user_id}).sort([("last_message_at", -1), ("updated_at", -1)])
        return [session async for session in cursor]

    async def touch_session(self, session_id: str) -> None:
        now = datetime.utcnow()
        await self._collection().update_one(
            {"_id": session_id},
            {"$set": {"last_message_at": now, "updated_at": now}},
        )
