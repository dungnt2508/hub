"""Intent repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.domain.intent import (
    Intent,
    IntentPattern,
    IntentHint,
    IntentAction,
)


class IntentRepository:
    """Repository for intent data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_intent(
        self,
        intent_id: UUID,
        tenant_id: UUID
    ) -> Optional[Intent]:
        """Get intent by ID"""
        stmt = text("""
            SELECT id, tenant_id, name, domain, priority, created_at, updated_at
            FROM intents
            WHERE id = :intent_id AND tenant_id = :tenant_id
        """)
        result = await self.session.execute(
            stmt,
            {"intent_id": intent_id, "tenant_id": tenant_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return Intent(
            id=row[0],
            tenant_id=row[1],
            name=row[2],
            domain=row[3],
            priority=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
    
    async def list_intents(
        self,
        tenant_id: UUID,
        domain: Optional[str] = None
    ) -> List[Intent]:
        """List intents for tenant"""
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id}
        
        if domain:
            conditions.append("domain = :domain")
            params["domain"] = domain
        
        where_clause = " AND ".join(conditions)
        
        stmt = text(f"""
            SELECT id, tenant_id, name, domain, priority, created_at, updated_at
            FROM intents
            WHERE {where_clause}
            ORDER BY priority DESC, name ASC
        """)
        result = await self.session.execute(stmt, params)
        rows = result.fetchall()
        
        return [
            Intent(
                id=row[0],
                tenant_id=row[1],
                name=row[2],
                domain=row[3],
                priority=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]
    
    async def get_intent_patterns(
        self,
        intent_id: UUID
    ) -> List[IntentPattern]:
        """Get patterns for intent"""
        stmt = text("""
            SELECT id, intent_id, type, pattern, weight, created_at
            FROM intent_patterns
            WHERE intent_id = :intent_id
            ORDER BY weight DESC, created_at ASC
        """)
        result = await self.session.execute(stmt, {"intent_id": intent_id})
        rows = result.fetchall()
        
        return [
            IntentPattern(
                id=row[0],
                intent_id=row[1],
                type=row[2],
                pattern=row[3],
                weight=row[4],
                created_at=row[5],
            )
            for row in rows
        ]
    
    async def get_intent_hints(
        self,
        intent_id: UUID
    ) -> List[IntentHint]:
        """Get hints for intent"""
        stmt = text("""
            SELECT id, intent_id, hint_text, created_at
            FROM intent_hints
            WHERE intent_id = :intent_id
            ORDER BY created_at ASC
        """)
        result = await self.session.execute(stmt, {"intent_id": intent_id})
        rows = result.fetchall()
        
        return [
            IntentHint(
                id=row[0],
                intent_id=row[1],
                hint_text=row[2],
                created_at=row[3],
            )
            for row in rows
        ]
    
    async def get_intent_actions(
        self,
        intent_id: UUID
    ) -> List[IntentAction]:
        """Get actions for intent"""
        stmt = text("""
            SELECT id, intent_id, action_type, config_json, priority, created_at
            FROM intent_actions
            WHERE intent_id = :intent_id
            ORDER BY priority DESC, created_at ASC
        """)
        result = await self.session.execute(stmt, {"intent_id": intent_id})
        rows = result.fetchall()
        
        return [
            IntentAction(
                id=row[0],
                intent_id=row[1],
                action_type=row[2],
                config_json=row[3],
                priority=row[4],
                created_at=row[5],
            )
            for row in rows
        ]
    
    async def find_intents_by_patterns(
        self,
        tenant_id: UUID,
        query_text: str
    ) -> List[Intent]:
        """Find intents that match patterns in query text"""
        # This is a simplified version - in production, you'd want more sophisticated matching
        stmt = text("""
            SELECT DISTINCT i.id, i.tenant_id, i.name, i.domain, i.priority, i.created_at, i.updated_at
            FROM intents i
            INNER JOIN intent_patterns ip ON i.id = ip.intent_id
            WHERE i.tenant_id = :tenant_id
              AND (
                (ip.type = 'keyword' AND LOWER(:query_text) LIKE '%' || LOWER(ip.pattern) || '%')
                OR (ip.type = 'phrase' AND LOWER(:query_text) LIKE '%' || LOWER(ip.pattern) || '%')
                OR (ip.type = 'regex' AND :query_text ~ ip.pattern)
              )
            ORDER BY i.priority DESC, i.name ASC
        """)
        result = await self.session.execute(
            stmt,
            {"tenant_id": tenant_id, "query_text": query_text}
        )
        rows = result.fetchall()
        
        return [
            Intent(
                id=row[0],
                tenant_id=row[1],
                name=row[2],
                domain=row[3],
                priority=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]
