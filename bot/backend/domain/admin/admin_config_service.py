"""
Admin Config Service - Business logic for config CRUD operations
"""
import json
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from ...shared.logger import logger
from ...shared.exceptions import NotFoundError, ValidationError
from ...infrastructure.database_client import database_client
from ...infrastructure.config_loader import config_loader
from .audit_log_service import audit_log_service
from ...schemas.admin_config_types import (
    PatternRuleCreate,
    PatternRuleUpdate,
    PatternRuleResponse,
    KeywordHintCreate,
    KeywordHintUpdate,
    KeywordHintResponse,
    RoutingRuleCreate,
    RoutingRuleUpdate,
    RoutingRuleResponse,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    ToolPermissionCreate,
    ToolPermissionUpdate,
    ToolPermissionResponse,
    GuardrailCreate,
    GuardrailUpdate,
    GuardrailResponse,
)


class AdminConfigService:
    """Service for admin config CRUD operations"""
    
    def __init__(self):
        self.db = database_client
        self.config_loader = config_loader
        self.audit_log = audit_log_service
    
    # ==================== Pattern Rules ====================
    
    async def create_pattern_rule(
        self,
        rule: PatternRuleCreate,
        created_by: UUID
    ) -> PatternRuleResponse:
        """Create pattern rule"""
        pool = self.db.pool
        
        rule_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO pattern_rules (
                    id, tenant_id, rule_name, enabled, pattern_regex, pattern_flags,
                    target_domain, target_intent, intent_type, slots_extraction,
                    priority, scope, scope_filter, description, created_by,
                    created_at, updated_at, version
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, 1
                ) RETURNING *
                """,
                rule_id,
                rule.tenant_id,
                rule.rule_name,
                rule.enabled,
                rule.pattern_regex,
                rule.pattern_flags,
                rule.target_domain,
                rule.target_intent,
                rule.intent_type,
                json.dumps(rule.slots_extraction) if rule.slots_extraction else None,
                rule.priority,
                rule.scope,
                json.dumps(rule.scope_filter) if rule.scope_filter else None,
                rule.description,
                created_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("pattern_rules", rule.tenant_id)
        
        # Audit log
        result = self._pattern_rule_from_row(row)
        await self.audit_log.log_config_change(
            config_type="pattern_rule",
            config_id=result.id,
            config_name=result.rule_name,
            action="create",
            changed_by=created_by,
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def get_pattern_rule(self, rule_id: UUID) -> PatternRuleResponse:
        """Get pattern rule by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM pattern_rules WHERE id = $1",
                rule_id
            )
        
        if not row:
            raise NotFoundError(f"Pattern rule {rule_id} not found")
        
        return self._pattern_rule_from_row(row)
    
    async def list_pattern_rules(
        self,
        tenant_id: Optional[UUID] = None,
        enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List pattern rules"""
        pool = self.db.pool
        
        query = "SELECT * FROM pattern_rules WHERE 1=1"
        params = []
        param_idx = 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if enabled is not None:
            query += f" AND enabled = ${param_idx}"
            params.append(enabled)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY priority DESC, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._pattern_rule_from_row(row) for row in rows]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_pattern_rule(
        self,
        rule_id: UUID,
        rule: PatternRuleUpdate,
        updated_by: UUID
    ) -> PatternRuleResponse:
        """Update pattern rule"""
        pool = self.db.pool
        
        # Get existing rule
        existing = await self.get_pattern_rule(rule_id)
        
        # Build update query
        updates = []
        params = []
        param_idx = 1
        
        if rule.rule_name is not None:
            updates.append(f"rule_name = ${param_idx}")
            params.append(rule.rule_name)
            param_idx += 1
        
        if rule.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(rule.enabled)
            param_idx += 1
        
        if rule.pattern_regex is not None:
            updates.append(f"pattern_regex = ${param_idx}")
            params.append(rule.pattern_regex)
            param_idx += 1
        
        if rule.pattern_flags is not None:
            updates.append(f"pattern_flags = ${param_idx}")
            params.append(rule.pattern_flags)
            param_idx += 1
        
        if rule.target_domain is not None:
            updates.append(f"target_domain = ${param_idx}")
            params.append(rule.target_domain)
            param_idx += 1
        
        if rule.target_intent is not None:
            updates.append(f"target_intent = ${param_idx}")
            params.append(rule.target_intent)
            param_idx += 1
        
        if rule.intent_type is not None:
            updates.append(f"intent_type = ${param_idx}")
            params.append(rule.intent_type)
            param_idx += 1
        
        if rule.slots_extraction is not None:
            updates.append(f"slots_extraction = ${param_idx}")
            params.append(json.dumps(rule.slots_extraction))
            param_idx += 1
        
        if rule.priority is not None:
            updates.append(f"priority = ${param_idx}")
            params.append(rule.priority)
            param_idx += 1
        
        if rule.scope is not None:
            updates.append(f"scope = ${param_idx}")
            params.append(rule.scope)
            param_idx += 1
        
        if rule.scope_filter is not None:
            updates.append(f"scope_filter = ${param_idx}")
            params.append(json.dumps(rule.scope_filter))
            param_idx += 1
        
        if rule.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(rule.description)
            param_idx += 1
        
        if not updates:
            return existing
        
        # Add updated_at
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        # Add version increment
        updates.append(f"version = version + 1")
        
        # Add rule_id to params
        params.append(rule_id)
        
        query = f"""
            UPDATE pattern_rules
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        
        if not row:
            raise NotFoundError(f"Pattern rule {rule_id} not found")
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("pattern_rules", existing.tenant_id)
        
        # Audit log
        result = self._pattern_rule_from_row(row)
        await self.audit_log.log_config_change(
            config_type="pattern_rule",
            config_id=result.id,
            config_name=result.rule_name,
            action="update",
            changed_by=updated_by,
            old_value=existing.dict(),
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def delete_pattern_rule(self, rule_id: UUID, changed_by: Optional[UUID] = None):
        """Delete pattern rule"""
        existing = await self.get_pattern_rule(rule_id)
        
        if changed_by is None:
            changed_by = UUID("00000000-0000-0000-0000-000000000001")  # TODO: Get from context
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM pattern_rules WHERE id = $1",
                rule_id
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("pattern_rules", existing.tenant_id)
        
        # Audit log
        await self.audit_log.log_config_change(
            config_type="pattern_rule",
            config_id=rule_id,
            config_name=existing.rule_name,
            action="delete",
            changed_by=changed_by,
            old_value=existing.dict(),
            tenant_id=existing.tenant_id,
        )
    
    async def enable_pattern_rule(self, rule_id: UUID, changed_by: Optional[UUID] = None) -> PatternRuleResponse:
        """Enable pattern rule"""
        if changed_by is None:
            changed_by = uuid4()  # TODO: Get from auth context
        
        existing = await self.get_pattern_rule(rule_id)
        result = await self.update_pattern_rule(
            rule_id,
            PatternRuleUpdate(enabled=True),
            changed_by
        )
        
        # Additional audit log for enable action
        await self.audit_log.log_config_change(
            config_type="pattern_rule",
            config_id=rule_id,
            config_name=existing.rule_name,
            action="enable",
            changed_by=changed_by,
            old_value={"enabled": False},
            new_value={"enabled": True},
            tenant_id=existing.tenant_id,
        )
        
        return result
    
    async def disable_pattern_rule(self, rule_id: UUID, changed_by: Optional[UUID] = None) -> PatternRuleResponse:
        """Disable pattern rule"""
        if changed_by is None:
            changed_by = uuid4()  # TODO: Get from auth context
        
        existing = await self.get_pattern_rule(rule_id)
        result = await self.update_pattern_rule(
            rule_id,
            PatternRuleUpdate(enabled=False),
            changed_by
        )
        
        # Additional audit log for disable action
        await self.audit_log.log_config_change(
            config_type="pattern_rule",
            config_id=rule_id,
            config_name=existing.rule_name,
            action="disable",
            changed_by=changed_by,
            old_value={"enabled": True},
            new_value={"enabled": False},
            tenant_id=existing.tenant_id,
        )
        
        return result
    
    def _pattern_rule_from_row(self, row) -> PatternRuleResponse:
        """Convert database row to PatternRuleResponse"""
        return PatternRuleResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            rule_name=row["rule_name"],
            enabled=row["enabled"],
            pattern_regex=row["pattern_regex"],
            pattern_flags=row["pattern_flags"],
            target_domain=row["target_domain"],
            target_intent=row["target_intent"],
            intent_type=row["intent_type"],
            slots_extraction=json.loads(row["slots_extraction"]) if row["slots_extraction"] else None,
            priority=row["priority"],
            scope=row["scope"],
            scope_filter=json.loads(row["scope_filter"]) if row["scope_filter"] else None,
            description=row["description"],
            version=row["version"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    # ==================== Keyword Hints ====================
    
    async def create_keyword_hint(
        self,
        hint: KeywordHintCreate,
        created_by: UUID
    ) -> KeywordHintResponse:
        """Create keyword hint"""
        pool = self.db.pool
        
        hint_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO keyword_hints (
                    id, tenant_id, rule_name, enabled, domain, keywords,
                    scope, scope_filter, description, created_by,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                ) RETURNING *
                """,
                hint_id,
                hint.tenant_id,
                hint.rule_name,
                hint.enabled,
                hint.domain,
                json.dumps(hint.keywords),
                hint.scope,
                json.dumps(hint.scope_filter) if hint.scope_filter else None,
                hint.description,
                created_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("keyword_hints", hint.tenant_id)
        
        # Audit log
        result = self._keyword_hint_from_row(row)
        await self.audit_log.log_config_change(
            config_type="keyword_hint",
            config_id=result.id,
            config_name=result.rule_name,
            action="create",
            changed_by=created_by,
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def get_keyword_hint(self, hint_id: UUID) -> KeywordHintResponse:
        """Get keyword hint by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM keyword_hints WHERE id = $1",
                hint_id
            )
        
        if not row:
            raise NotFoundError(f"Keyword hint {hint_id} not found")
        
        return self._keyword_hint_from_row(row)
    
    async def list_keyword_hints(
        self,
        tenant_id: Optional[UUID] = None,
        enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List keyword hints"""
        pool = self.db.pool
        
        query = "SELECT * FROM keyword_hints WHERE 1=1"
        params = []
        param_idx = 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if enabled is not None:
            query += f" AND enabled = ${param_idx}"
            params.append(enabled)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY domain, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._keyword_hint_from_row(row) for row in rows]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_keyword_hint(
        self,
        hint_id: UUID,
        hint: KeywordHintUpdate,
        updated_by: UUID
    ) -> KeywordHintResponse:
        """Update keyword hint"""
        pool = self.db.pool
        
        existing = await self.get_keyword_hint(hint_id)
        
        updates = []
        params = []
        param_idx = 1
        
        if hint.rule_name is not None:
            updates.append(f"rule_name = ${param_idx}")
            params.append(hint.rule_name)
            param_idx += 1
        
        if hint.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(hint.enabled)
            param_idx += 1
        
        if hint.domain is not None:
            updates.append(f"domain = ${param_idx}")
            params.append(hint.domain)
            param_idx += 1
        
        if hint.keywords is not None:
            updates.append(f"keywords = ${param_idx}")
            params.append(json.dumps(hint.keywords))
            param_idx += 1
        
        if hint.scope is not None:
            updates.append(f"scope = ${param_idx}")
            params.append(hint.scope)
            param_idx += 1
        
        if hint.scope_filter is not None:
            updates.append(f"scope_filter = ${param_idx}")
            params.append(json.dumps(hint.scope_filter))
            param_idx += 1
        
        if hint.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(hint.description)
            param_idx += 1
        
        if not updates:
            return existing
        
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        params.append(hint_id)
        
        query = f"""
            UPDATE keyword_hints
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        
        if not row:
            raise NotFoundError(f"Keyword hint {hint_id} not found")
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("keyword_hints", existing.tenant_id)
        
        # Audit log
        result = self._keyword_hint_from_row(row)
        await self.audit_log.log_config_change(
            config_type="keyword_hint",
            config_id=result.id,
            config_name=result.rule_name,
            action="update",
            changed_by=updated_by,
            old_value=existing.dict(),
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def delete_keyword_hint(self, hint_id: UUID, changed_by: Optional[UUID] = None):
        """Delete keyword hint"""
        existing = await self.get_keyword_hint(hint_id)
        
        if changed_by is None:
            changed_by = UUID("00000000-0000-0000-0000-000000000001")  # TODO: Get from context
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM keyword_hints WHERE id = $1",
                hint_id
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("keyword_hints", existing.tenant_id)
        
        # Audit log
        await self.audit_log.log_config_change(
            config_type="keyword_hint",
            config_id=hint_id,
            config_name=existing.rule_name,
            action="delete",
            changed_by=changed_by,
            old_value=existing.dict(),
            tenant_id=existing.tenant_id,
        )
    
    def _keyword_hint_from_row(self, row) -> KeywordHintResponse:
        """Convert database row to KeywordHintResponse"""
        return KeywordHintResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            rule_name=row["rule_name"],
            enabled=row["enabled"],
            domain=row["domain"],
            keywords=json.loads(row["keywords"]) if row["keywords"] else {},
            scope=row["scope"],
            scope_filter=json.loads(row["scope_filter"]) if row["scope_filter"] else None,
            description=row["description"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    # ==================== Routing Rules ====================
    
    async def create_routing_rule(
        self,
        rule: RoutingRuleCreate,
        created_by: UUID
    ) -> RoutingRuleResponse:
        """Create routing rule"""
        pool = self.db.pool
        
        rule_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO routing_rules (
                    id, tenant_id, rule_name, enabled, intent_pattern,
                    target_domain, target_agent, target_workflow,
                    priority, fallback_chain, scope, scope_filter,
                    description, created_by, created_at, updated_at, version
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, 1
                ) RETURNING *
                """,
                rule_id,
                rule.tenant_id,
                rule.rule_name,
                rule.enabled,
                json.dumps(rule.intent_pattern),
                rule.target_domain,
                rule.target_agent,
                json.dumps(rule.target_workflow) if rule.target_workflow else None,
                rule.priority,
                json.dumps(rule.fallback_chain) if rule.fallback_chain else None,
                rule.scope,
                json.dumps(rule.scope_filter) if rule.scope_filter else None,
                rule.description,
                created_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("routing_rules", rule.tenant_id)
        
        # Audit log
        result = self._routing_rule_from_row(row)
        await self.audit_log.log_config_change(
            config_type="routing_rule",
            config_id=result.id,
            config_name=result.rule_name,
            action="create",
            changed_by=created_by,
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def get_routing_rule(self, rule_id: UUID) -> RoutingRuleResponse:
        """Get routing rule by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM routing_rules WHERE id = $1",
                rule_id
            )
        
        if not row:
            raise NotFoundError(f"Routing rule {rule_id} not found")
        
        return self._routing_rule_from_row(row)
    
    async def list_routing_rules(
        self,
        tenant_id: Optional[UUID] = None,
        enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List routing rules"""
        pool = self.db.pool
        
        query = "SELECT * FROM routing_rules WHERE 1=1"
        params = []
        param_idx = 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if enabled is not None:
            query += f" AND enabled = ${param_idx}"
            params.append(enabled)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY priority DESC, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._routing_rule_from_row(row) for row in rows]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_routing_rule(
        self,
        rule_id: UUID,
        rule: RoutingRuleUpdate,
        updated_by: UUID
    ) -> RoutingRuleResponse:
        """Update routing rule"""
        pool = self.db.pool
        
        existing = await self.get_routing_rule(rule_id)
        
        updates = []
        params = []
        param_idx = 1
        
        if rule.rule_name is not None:
            updates.append(f"rule_name = ${param_idx}")
            params.append(rule.rule_name)
            param_idx += 1
        
        if rule.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(rule.enabled)
            param_idx += 1
        
        if rule.intent_pattern is not None:
            updates.append(f"intent_pattern = ${param_idx}")
            params.append(json.dumps(rule.intent_pattern))
            param_idx += 1
        
        if rule.target_domain is not None:
            updates.append(f"target_domain = ${param_idx}")
            params.append(rule.target_domain)
            param_idx += 1
        
        if rule.target_agent is not None:
            updates.append(f"target_agent = ${param_idx}")
            params.append(rule.target_agent)
            param_idx += 1
        
        if rule.target_workflow is not None:
            updates.append(f"target_workflow = ${param_idx}")
            params.append(json.dumps(rule.target_workflow))
            param_idx += 1
        
        if rule.priority is not None:
            updates.append(f"priority = ${param_idx}")
            params.append(rule.priority)
            param_idx += 1
        
        if rule.fallback_chain is not None:
            updates.append(f"fallback_chain = ${param_idx}")
            params.append(json.dumps(rule.fallback_chain))
            param_idx += 1
        
        if rule.scope is not None:
            updates.append(f"scope = ${param_idx}")
            params.append(rule.scope)
            param_idx += 1
        
        if rule.scope_filter is not None:
            updates.append(f"scope_filter = ${param_idx}")
            params.append(json.dumps(rule.scope_filter))
            param_idx += 1
        
        if rule.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(rule.description)
            param_idx += 1
        
        if not updates:
            return existing
        
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        updates.append(f"version = version + 1")
        
        params.append(rule_id)
        
        query = f"""
            UPDATE routing_rules
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        
        if not row:
            raise NotFoundError(f"Routing rule {rule_id} not found")
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("routing_rules", existing.tenant_id)
        
        # Audit log
        result = self._routing_rule_from_row(row)
        await self.audit_log.log_config_change(
            config_type="routing_rule",
            config_id=result.id,
            config_name=result.rule_name,
            action="update",
            changed_by=updated_by,
            old_value=existing.dict(),
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def delete_routing_rule(self, rule_id: UUID, changed_by: Optional[UUID] = None):
        """Delete routing rule"""
        existing = await self.get_routing_rule(rule_id)
        
        if changed_by is None:
            changed_by = UUID("00000000-0000-0000-0000-000000000001")  # TODO: Get from context
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM routing_rules WHERE id = $1",
                rule_id
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("routing_rules", existing.tenant_id)
        
        # Audit log
        await self.audit_log.log_config_change(
            config_type="routing_rule",
            config_id=rule_id,
            config_name=existing.rule_name,
            action="delete",
            changed_by=changed_by,
            old_value=existing.dict(),
            tenant_id=existing.tenant_id,
        )
    
    def _routing_rule_from_row(self, row) -> RoutingRuleResponse:
        """Convert database row to RoutingRuleResponse"""
        return RoutingRuleResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            rule_name=row["rule_name"],
            enabled=row["enabled"],
            intent_pattern=json.loads(row["intent_pattern"]) if row["intent_pattern"] else {},
            target_domain=row["target_domain"],
            target_agent=row["target_agent"],
            target_workflow=json.loads(row["target_workflow"]) if row["target_workflow"] else None,
            priority=row["priority"],
            fallback_chain=json.loads(row["fallback_chain"]) if row["fallback_chain"] else None,
            scope=row["scope"],
            scope_filter=json.loads(row["scope_filter"]) if row["scope_filter"] else None,
            description=row["description"],
            version=row["version"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    # ==================== Prompt Templates ====================
    
    async def create_prompt_template(
        self,
        template: PromptTemplateCreate,
        created_by: UUID
    ) -> PromptTemplateResponse:
        """Create prompt template"""
        pool = self.db.pool
        
        template_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO prompt_templates (
                    id, tenant_id, template_name, template_type, domain, agent,
                    enabled, template_text, variables, version, is_active,
                    description, created_by, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, 1, $10, $11, $12, $13, $14
                ) RETURNING *
                """,
                template_id,
                template.tenant_id,
                template.template_name,
                template.template_type,
                template.domain,
                template.agent,
                template.enabled,
                template.template_text,
                json.dumps(template.variables) if template.variables else None,
                template.enabled,  # is_active = enabled initially
                template.description,
                created_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("prompt_templates", template.tenant_id)
        
        # Audit log
        result = self._prompt_template_from_row(row)
        await self.audit_log.log_config_change(
            config_type="prompt_template",
            config_id=result.id,
            config_name=result.template_name,
            action="create",
            changed_by=created_by,
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def get_prompt_template(self, template_id: UUID) -> PromptTemplateResponse:
        """Get prompt template by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM prompt_templates WHERE id = $1 AND is_active = true",
                template_id
            )
        
        if not row:
            raise NotFoundError(f"Prompt template {template_id} not found")
        
        return self._prompt_template_from_row(row)
    
    async def list_prompt_templates(
        self,
        tenant_id: Optional[UUID] = None,
        template_type: Optional[str] = None,
        domain: Optional[str] = None,
        agent: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List prompt templates"""
        pool = self.db.pool
        
        query = "SELECT * FROM prompt_templates WHERE enabled = true"
        params = []
        param_idx = 1
        
        if active_only:
            query += f" AND is_active = ${param_idx}"
            params.append(True)
            param_idx += 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if template_type:
            query += f" AND template_type = ${param_idx}"
            params.append(template_type)
            param_idx += 1
        
        if domain:
            query += f" AND (domain = ${param_idx} OR domain IS NULL)"
            params.append(domain)
            param_idx += 1
        
        if agent:
            query += f" AND (agent = ${param_idx} OR agent IS NULL)"
            params.append(agent)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY domain NULLS LAST, agent NULLS LAST, template_name LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._prompt_template_from_row(row) for row in rows]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_prompt_template(
        self,
        template_id: UUID,
        template: PromptTemplateUpdate,
        updated_by: UUID
    ) -> PromptTemplateResponse:
        """Update prompt template (creates new version)"""
        pool = self.db.pool
        
        existing = await self.get_prompt_template(template_id)
        
        # Create new version instead of updating existing
        new_template_id = uuid4()
        now = datetime.utcnow()
        
        # Deactivate old version
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE prompt_templates SET is_active = false WHERE id = $1",
                template_id
            )
        
        # Get max version for this template name
        async with pool.acquire() as conn:
            max_version = await conn.fetchval(
                """
                SELECT MAX(version) FROM prompt_templates
                WHERE tenant_id = $1 AND template_name = $2
                """,
                existing.tenant_id,
                existing.template_name
            ) or 0
        
        # Create new version
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO prompt_templates (
                    id, tenant_id, template_name, template_type, domain, agent,
                    enabled, template_text, variables, version, is_active,
                    description, created_by, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true, $11, $12, $13, $14
                ) RETURNING *
                """,
                new_template_id,
                existing.tenant_id,
                template.template_name if template.template_name else existing.template_name,
                existing.template_type,
                existing.domain,
                existing.agent,
                template.enabled if template.enabled is not None else existing.enabled,
                template.template_text if template.template_text else existing.template_text,
                json.dumps(template.variables) if template.variables else existing.variables,
                max_version + 1,
                template.description if template.description else existing.description,
                updated_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("prompt_templates", existing.tenant_id)
        
        # Audit log
        result = self._prompt_template_from_row(row)
        await self.audit_log.log_config_change(
            config_type="prompt_template",
            config_id=result.id,
            config_name=result.template_name,
            action="update",
            changed_by=updated_by,
            old_value=existing.dict(),
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def list_template_versions(
        self,
        template_id: UUID
    ) -> List[Dict[str, Any]]:
        """List all versions of a template"""
        pool = self.db.pool
        
        # Get template name from ID
        existing = await self.get_prompt_template(template_id)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, version, template_text, is_active, created_at, created_by
                FROM prompt_templates
                WHERE tenant_id = $1 AND template_name = $2
                ORDER BY version DESC
                """,
                existing.tenant_id,
                existing.template_name
            )
        
        return [
            {
                "id": row["id"],
                "version": row["version"],
                "template_text": row["template_text"],
                "is_active": row["is_active"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "created_by": str(row["created_by"]) if row["created_by"] else None,
            }
            for row in rows
        ]
    
    async def rollback_template_version(
        self,
        template_id: UUID,
        target_version: int,
        updated_by: UUID
    ) -> PromptTemplateResponse:
        """Rollback template to a previous version"""
        pool = self.db.pool
        
        existing = await self.get_prompt_template(template_id)
        
        # Get target version
        async with pool.acquire() as conn:
            target_row = await conn.fetchrow(
                """
                SELECT * FROM prompt_templates
                WHERE tenant_id = $1 AND template_name = $2 AND version = $3
                """,
                existing.tenant_id,
                existing.template_name,
                target_version
            )
        
        if not target_row:
            raise NotFoundError(f"Version {target_version} not found for template {existing.template_name}")
        
        # Deactivate current version
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE prompt_templates SET is_active = false WHERE id = $1",
                template_id
            )
        
        # Activate target version
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE prompt_templates SET is_active = true, updated_at = $1 WHERE id = $2",
                datetime.utcnow(),
                target_row["id"]
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("prompt_templates", existing.tenant_id)
        
        # Audit log
        result = self._prompt_template_from_row(target_row)
        await self.audit_log.log_config_change(
            config_type="prompt_template",
            config_id=result.id,
            config_name=result.template_name,
            action="rollback",
            changed_by=updated_by,
            old_value={"version": existing.version},
            new_value={"version": target_version},
            tenant_id=result.tenant_id,
            reason=f"Rollback to version {target_version}",
        )
        
        return result
    
    async def delete_prompt_template(self, template_id: UUID, changed_by: Optional[UUID] = None):
        """Delete prompt template (all versions)"""
        existing = await self.get_prompt_template(template_id)
        
        if changed_by is None:
            changed_by = UUID("00000000-0000-0000-0000-000000000001")  # TODO: Get from context
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            # Handle NULL tenant_id case
            if existing.tenant_id is None:
                await conn.execute(
                    """
                    DELETE FROM prompt_templates
                    WHERE tenant_id IS NULL AND template_name = $1
                    """,
                    existing.template_name
                )
            else:
                await conn.execute(
                    """
                    DELETE FROM prompt_templates
                    WHERE tenant_id = $1 AND template_name = $2
                    """,
                    existing.tenant_id,
                    existing.template_name
                )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("prompt_templates", existing.tenant_id)
        
        # Audit log
        await self.audit_log.log_config_change(
            config_type="prompt_template",
            config_id=template_id,
            config_name=existing.template_name,
            action="delete",
            changed_by=changed_by,
            old_value=existing.dict(),
            tenant_id=existing.tenant_id,
        )
    
    def _prompt_template_from_row(self, row) -> PromptTemplateResponse:
        """Convert database row to PromptTemplateResponse"""
        return PromptTemplateResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            rule_name=row["template_name"],  # Map template_name to rule_name for ConfigBase compatibility
            template_name=row["template_name"],
            template_type=row["template_type"],
            domain=row["domain"],
            agent=row["agent"],
            enabled=row["enabled"],
            template_text=row["template_text"],
            variables=json.loads(row["variables"]) if row["variables"] else None,
            version=row["version"],
            is_active=row["is_active"],
            scope=row.get("scope", "global"),  # Default if not in schema
            scope_filter=None,  # Not in prompt_templates table
            description=row["description"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    # ==================== Tool Permissions ====================
    
    async def create_tool_permission(
        self,
        permission: ToolPermissionCreate,
        created_by: UUID
    ) -> ToolPermissionResponse:
        """Create tool permission"""
        pool = self.db.pool
        
        permission_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tool_permissions (
                    id, tenant_id, agent_name, tool_name, enabled,
                    allowed_contexts, rate_limit, required_params,
                    description, created_by, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                ) RETURNING *
                """,
                permission_id,
                permission.tenant_id,
                permission.agent_name,
                permission.tool_name,
                permission.enabled,
                json.dumps(permission.allowed_contexts) if permission.allowed_contexts else None,
                permission.rate_limit,
                json.dumps(permission.required_params) if permission.required_params else None,
                permission.description,
                created_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("tool_permissions", permission.tenant_id)
        
        # Audit log
        result = self._tool_permission_from_row(row)
        await self.audit_log.log_config_change(
            config_type="tool_permission",
            config_id=result.id,
            config_name=f"{result.agent_name}.{result.tool_name}",
            action="create",
            changed_by=created_by,
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def get_tool_permission(self, permission_id: UUID) -> ToolPermissionResponse:
        """Get tool permission by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tool_permissions WHERE id = $1",
                permission_id
            )
        
        if not row:
            raise NotFoundError(f"Tool permission {permission_id} not found")
        
        return self._tool_permission_from_row(row)
    
    async def list_tool_permissions(
        self,
        tenant_id: Optional[UUID] = None,
        agent_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List tool permissions"""
        pool = self.db.pool
        
        query = "SELECT * FROM tool_permissions WHERE 1=1"
        params = []
        param_idx = 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if agent_name:
            query += f" AND agent_name = ${param_idx}"
            params.append(agent_name)
            param_idx += 1
        
        if enabled is not None:
            query += f" AND enabled = ${param_idx}"
            params.append(enabled)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY agent_name, tool_name LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._tool_permission_from_row(row) for row in rows]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_tool_permission(
        self,
        permission_id: UUID,
        permission: ToolPermissionUpdate,
        updated_by: UUID
    ) -> ToolPermissionResponse:
        """Update tool permission"""
        pool = self.db.pool
        
        existing = await self.get_tool_permission(permission_id)
        
        updates = []
        params = []
        param_idx = 1
        
        if permission.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(permission.enabled)
            param_idx += 1
        
        if permission.allowed_contexts is not None:
            updates.append(f"allowed_contexts = ${param_idx}")
            params.append(json.dumps(permission.allowed_contexts))
            param_idx += 1
        
        if permission.rate_limit is not None:
            updates.append(f"rate_limit = ${param_idx}")
            params.append(permission.rate_limit)
            param_idx += 1
        
        if permission.required_params is not None:
            updates.append(f"required_params = ${param_idx}")
            params.append(json.dumps(permission.required_params))
            param_idx += 1
        
        if permission.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(permission.description)
            param_idx += 1
        
        if not updates:
            return existing
        
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        params.append(permission_id)
        
        query = f"""
            UPDATE tool_permissions
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        
        if not row:
            raise NotFoundError(f"Tool permission {permission_id} not found")
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("tool_permissions", existing.tenant_id)
        
        # Audit log
        result = self._tool_permission_from_row(row)
        await self.audit_log.log_config_change(
            config_type="tool_permission",
            config_id=result.id,
            config_name=f"{result.agent_name}.{result.tool_name}",
            action="update",
            changed_by=updated_by,
            old_value=existing.dict(),
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def delete_tool_permission(self, permission_id: UUID, changed_by: Optional[UUID] = None):
        """Delete tool permission"""
        existing = await self.get_tool_permission(permission_id)
        
        if changed_by is None:
            changed_by = UUID("00000000-0000-0000-0000-000000000001")  # TODO: Get from context
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM tool_permissions WHERE id = $1",
                permission_id
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("tool_permissions", existing.tenant_id)
        
        # Audit log
        await self.audit_log.log_config_change(
            config_type="tool_permission",
            config_id=permission_id,
            config_name=f"{existing.agent_name}.{existing.tool_name}",
            action="delete",
            changed_by=changed_by,
            old_value=existing.dict(),
            tenant_id=existing.tenant_id,
        )
    
    def _tool_permission_from_row(self, row) -> ToolPermissionResponse:
        """Convert database row to ToolPermissionResponse"""
        return ToolPermissionResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            agent_name=row["agent_name"],
            tool_name=row["tool_name"],
            enabled=row["enabled"],
            allowed_contexts=json.loads(row["allowed_contexts"]) if row["allowed_contexts"] else None,
            rate_limit=row["rate_limit"],
            required_params=json.loads(row["required_params"]) if row["required_params"] else None,
            description=row["description"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    # ==================== Guardrails ====================
    
    async def create_guardrail(
        self,
        guardrail: GuardrailCreate,
        created_by: UUID
    ) -> GuardrailResponse:
        """Create guardrail"""
        pool = self.db.pool
        
        guardrail_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO guardrails (
                    id, tenant_id, rule_name, rule_type, enabled,
                    trigger_condition, action, action_params,
                    priority, scope, scope_filter, description,
                    created_by, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                ) RETURNING *
                """,
                guardrail_id,
                guardrail.tenant_id,
                guardrail.rule_name,
                guardrail.rule_type,
                guardrail.enabled,
                json.dumps(guardrail.trigger_condition),
                guardrail.action,
                json.dumps(guardrail.action_params) if guardrail.action_params else None,
                guardrail.priority,
                guardrail.scope,
                json.dumps(guardrail.scope_filter) if guardrail.scope_filter else None,
                guardrail.description,
                created_by,
                now,
                now,
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("guardrails", guardrail.tenant_id)
        
        # Audit log
        result = self._guardrail_from_row(row)
        await self.audit_log.log_config_change(
            config_type="guardrail",
            config_id=result.id,
            config_name=result.rule_name,
            action="create",
            changed_by=created_by,
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def get_guardrail(self, guardrail_id: UUID) -> GuardrailResponse:
        """Get guardrail by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM guardrails WHERE id = $1",
                guardrail_id
            )
        
        if not row:
            raise NotFoundError(f"Guardrail {guardrail_id} not found")
        
        return self._guardrail_from_row(row)
    
    async def list_guardrails(
        self,
        tenant_id: Optional[UUID] = None,
        rule_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List guardrails"""
        pool = self.db.pool
        
        query = "SELECT * FROM guardrails WHERE 1=1"
        params = []
        param_idx = 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if rule_type:
            query += f" AND rule_type = ${param_idx}"
            params.append(rule_type)
            param_idx += 1
        
        if enabled is not None:
            query += f" AND enabled = ${param_idx}"
            params.append(enabled)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY priority DESC, created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._guardrail_from_row(row) for row in rows]
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_guardrail(
        self,
        guardrail_id: UUID,
        guardrail: GuardrailUpdate,
        updated_by: UUID
    ) -> GuardrailResponse:
        """Update guardrail"""
        pool = self.db.pool
        
        existing = await self.get_guardrail(guardrail_id)
        
        updates = []
        params = []
        param_idx = 1
        
        if guardrail.rule_name is not None:
            updates.append(f"rule_name = ${param_idx}")
            params.append(guardrail.rule_name)
            param_idx += 1
        
        if guardrail.enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(guardrail.enabled)
            param_idx += 1
        
        if guardrail.rule_type is not None:
            updates.append(f"rule_type = ${param_idx}")
            params.append(guardrail.rule_type)
            param_idx += 1
        
        if guardrail.trigger_condition is not None:
            updates.append(f"trigger_condition = ${param_idx}")
            params.append(json.dumps(guardrail.trigger_condition))
            param_idx += 1
        
        if guardrail.action is not None:
            updates.append(f"action = ${param_idx}")
            params.append(guardrail.action)
            param_idx += 1
        
        if guardrail.action_params is not None:
            updates.append(f"action_params = ${param_idx}")
            params.append(json.dumps(guardrail.action_params))
            param_idx += 1
        
        if guardrail.priority is not None:
            updates.append(f"priority = ${param_idx}")
            params.append(guardrail.priority)
            param_idx += 1
        
        if guardrail.scope is not None:
            updates.append(f"scope = ${param_idx}")
            params.append(guardrail.scope)
            param_idx += 1
        
        if guardrail.scope_filter is not None:
            updates.append(f"scope_filter = ${param_idx}")
            params.append(json.dumps(guardrail.scope_filter))
            param_idx += 1
        
        if guardrail.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(guardrail.description)
            param_idx += 1
        
        if not updates:
            return existing
        
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        params.append(guardrail_id)
        
        query = f"""
            UPDATE guardrails
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        
        if not row:
            raise NotFoundError(f"Guardrail {guardrail_id} not found")
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("guardrails", existing.tenant_id)
        
        # Audit log
        result = self._guardrail_from_row(row)
        await self.audit_log.log_config_change(
            config_type="guardrail",
            config_id=result.id,
            config_name=result.rule_name,
            action="update",
            changed_by=updated_by,
            old_value=existing.dict(),
            new_value=result.dict(),
            tenant_id=result.tenant_id,
        )
        
        return result
    
    async def delete_guardrail(self, guardrail_id: UUID, changed_by: Optional[UUID] = None):
        """Delete guardrail"""
        existing = await self.get_guardrail(guardrail_id)
        
        if changed_by is None:
            changed_by = UUID("00000000-0000-0000-0000-000000000001")  # TODO: Get from context
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM guardrails WHERE id = $1",
                guardrail_id
            )
        
        # Invalidate cache
        await self.config_loader.invalidate_cache("guardrails", existing.tenant_id)
        
        # Audit log
        await self.audit_log.log_config_change(
            config_type="guardrail",
            config_id=guardrail_id,
            config_name=existing.rule_name,
            action="delete",
            changed_by=changed_by,
            old_value=existing.dict(),
            tenant_id=existing.tenant_id,
        )
    
    def _guardrail_from_row(self, row) -> GuardrailResponse:
        """Convert database row to GuardrailResponse"""
        return GuardrailResponse(
            id=row["id"],
            tenant_id=row["tenant_id"],
            rule_name=row["rule_name"],
            enabled=row["enabled"],
            rule_type=row["rule_type"],
            trigger_condition=json.loads(row["trigger_condition"]) if row["trigger_condition"] else {},
            action=row["action"],
            action_params=json.loads(row["action_params"]) if row["action_params"] else None,
            priority=row["priority"],
            scope=row["scope"],
            scope_filter=json.loads(row["scope_filter"]) if row["scope_filter"] else None,
            description=row["description"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# Global service instance
admin_config_service = AdminConfigService()

