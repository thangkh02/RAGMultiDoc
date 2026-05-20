from app.models.session import SessionModel
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.utils.id_utils import generate_id


class SessionService:
    def __init__(self) -> None:
        self.session_repository = SessionRepository()
        self.message_repository = MessageRepository()

    async def create_session(self, user_id: str, title: str | None = None, description: str | None = None) -> SessionModel:
        session = SessionModel(id=generate_id("sess"), owner_user_id=user_id, title=title, description=description)
        await self.session_repository.create_session(session)
        return session

    async def list_sessions(self, user_id: str):
        return await self.session_repository.list_user_sessions(user_id)

    async def list_session_messages(self, session_id: str):
        return await self.message_repository.list_session_messages(session_id)

    async def touch_session(self, session_id: str) -> None:
        await self.session_repository.touch_session(session_id)
