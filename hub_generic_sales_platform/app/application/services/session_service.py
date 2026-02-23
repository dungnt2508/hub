"""Session and Turn Management Service"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories import SessionRepository, ConversationTurnRepository
from app.infrastructure.database.repositories import BotVersionRepository
from app.core.shared.exceptions import EntityNotFoundError
from app.core.shared.db_utils import transaction_scope


class SessionService:
    """Service to handle session lifecycle and conversation turns (SRP Refactor)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.turn_repo = ConversationTurnRepository(db)
        self.version_repo = BotVersionRepository(db)

    async def get_or_create_session(
        self, 
        tenant_id: str, 
        bot_id: str, 
        session_id: Optional[str] = None,
        channel_code: str = "webchat",
        ext_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ensures a session exists and returns session data + version_id.
        When session_id is provided (e.g. zalo_{user_id}), maps external user to runtime_session.
        ext_metadata stores channel-specific ids (zalo_user_id, messenger_id, etc.) for Monitor & reverse lookup.
        """
        async with transaction_scope(self.db):
            create_payload = {
                "bot_id": bot_id,
                "channel_code": channel_code,
                "lifecycle_state": "idle"
            }
            if ext_metadata:
                create_payload["ext_metadata"] = ext_metadata

            if not session_id:
                active_version = await self.version_repo.get_active_version(bot_id, tenant_id=tenant_id)
                if not active_version:
                    raise EntityNotFoundError("Bot", bot_id)
                create_payload["bot_version_id"] = str(active_version.id)
                session = await self.session_repo.create(create_payload, tenant_id=tenant_id)
                return {
                    "session_id": str(session.id),
                    "bot_version_id": str(active_version.id),
                    "session": session
                }
            else:
                session = await self.session_repo.get(session_id, tenant_id=tenant_id)
                if not session:
                    active_version = await self.version_repo.get_active_version(bot_id, tenant_id=tenant_id)
                    if not active_version:
                        raise EntityNotFoundError("Bot", bot_id)
                    create_payload["id"] = session_id
                    create_payload["bot_version_id"] = str(active_version.id)
                    session = await self.session_repo.create(create_payload, tenant_id=tenant_id)
                    # Merge ext_metadata nếu session đã tồn tại nhưng cần update
                elif ext_metadata:
                    merged = dict(session.ext_metadata or {})
                    merged.update(ext_metadata)
                    await self.session_repo.update(session, {"ext_metadata": merged}, tenant_id=tenant_id)
                    session = await self.session_repo.get(session_id, tenant_id=tenant_id)
                
                return {
                    "session_id": str(session.id),
                    "bot_version_id": str(session.bot_version_id),
                    "session": session
                }

    async def log_user_message(self, session_id: str, message: str):
        """Record user input turn"""
        async with transaction_scope(self.db):
            await self.turn_repo.create({
                "session_id": session_id,
                "speaker": "user",
                "message": message
            })

    async def log_bot_response(self, session_id: str, response: str):
        """Record bot response turn"""
        async with transaction_scope(self.db):
            await self.turn_repo.create({
                "session_id": session_id,
                "speaker": "bot",
                "message": response
            })
