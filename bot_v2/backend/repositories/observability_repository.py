"""Observability repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.domain.observability import ConversationLog, FailedQuery


class ObservabilityRepository:
    """Repository for observability data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_conversation_log(
        self,
        tenant_id: UUID,
        channel_id: Optional[UUID],
        intent: Optional[str],
        domain: Optional[str],
        success: bool
    ) -> ConversationLog:
        """Create conversation log"""
        from uuid import uuid4
        from datetime import datetime
        
        log_id = uuid4()
        stmt = text("""
            INSERT INTO conversation_logs (id, tenant_id, channel_id, intent, domain, success, created_at)
            VALUES (:id, :tenant_id, :channel_id, :intent, :domain, :success, :created_at)
            RETURNING id, tenant_id, channel_id, intent, domain, success, created_at
        """)
        result = await self.session.execute(
            stmt,
            {
                "id": log_id,
                "tenant_id": tenant_id,
                "channel_id": channel_id,
                "intent": intent,
                "domain": domain,
                "success": success,
                "created_at": datetime.utcnow(),
            }
        )
        await self.session.commit()
        row = result.fetchone()
        
        if not row:
            raise ValueError("Failed to create conversation log")
        
        return ConversationLog(
            id=row[0],
            tenant_id=row[1],
            channel_id=row[2],
            intent=row[3],
            domain=row[4],
            success=row[5],
            created_at=row[6],
        )
    
    async def list_conversation_logs(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConversationLog]:
        """List conversation logs"""
        stmt = text("""
            SELECT id, tenant_id, channel_id, intent, domain, success, created_at
            FROM conversation_logs
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self.session.execute(
            stmt,
            {"tenant_id": tenant_id, "limit": limit, "offset": offset}
        )
        rows = result.fetchall()
        
        return [
            ConversationLog(
                id=row[0],
                tenant_id=row[1],
                channel_id=row[2],
                intent=row[3],
                domain=row[4],
                success=row[5],
                created_at=row[6],
            )
            for row in rows
        ]
    
    async def create_failed_query(
        self,
        tenant_id: UUID,
        query: str,
        reason: Optional[str] = None
    ) -> FailedQuery:
        """Create failed query log"""
        from uuid import uuid4
        from datetime import datetime
        
        query_id = uuid4()
        stmt = text("""
            INSERT INTO failed_queries (id, tenant_id, query, reason, created_at)
            VALUES (:id, :tenant_id, :query, :reason, :created_at)
            RETURNING id, tenant_id, query, reason, created_at
        """)
        result = await self.session.execute(
            stmt,
            {
                "id": query_id,
                "tenant_id": tenant_id,
                "query": query,
                "reason": reason,
                "created_at": datetime.utcnow(),
            }
        )
        await self.session.commit()
        row = result.fetchone()
        
        if not row:
            raise ValueError("Failed to create failed query")
        
        return FailedQuery(
            id=row[0],
            tenant_id=row[1],
            query=row[2],
            reason=row[3],
            created_at=row[4],
        )
    
    async def list_failed_queries(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[FailedQuery]:
        """List failed queries"""
        stmt = text("""
            SELECT id, tenant_id, query, reason, created_at
            FROM failed_queries
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self.session.execute(
            stmt,
            {"tenant_id": tenant_id, "limit": limit, "offset": offset}
        )
        rows = result.fetchall()
        
        return [
            FailedQuery(
                id=row[0],
                tenant_id=row[1],
                query=row[2],
                reason=row[3],
                created_at=row[4],
            )
            for row in rows
        ]
