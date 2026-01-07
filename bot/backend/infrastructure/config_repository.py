"""
Config Repository - Database queries for config domains
"""
import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

from ..shared.logger import logger
from .database_client import database_client


class ConfigRepository:
    """Repository for config domain queries"""
    
    async def get_pattern_rules(
        self,
        tenant_id: Optional[UUID] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get pattern rules for tenant (or global if tenant_id is None)"""
        pool = database_client.pool
        
        query = """
            SELECT 
                id, tenant_id, rule_name, enabled, pattern_regex, pattern_flags,
                target_domain, target_intent, intent_type, slots_extraction,
                priority, scope, scope_filter, description, created_by,
                created_at, updated_at, version
            FROM pattern_rules
            WHERE enabled = $1
        """
        params = [enabled_only]
        
        if tenant_id:
            query += " AND (tenant_id = $2 OR tenant_id IS NULL)"
            params.append(tenant_id)
        else:
            query += " AND tenant_id IS NULL"
        
        query += " ORDER BY priority DESC, created_at ASC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def get_keyword_hints(
        self,
        tenant_id: Optional[UUID] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get keyword hints for tenant (or global)"""
        pool = database_client.pool
        
        query = """
            SELECT 
                id, tenant_id, rule_name, enabled, domain, keywords,
                scope, scope_filter, description, created_by,
                created_at, updated_at
            FROM keyword_hints
            WHERE enabled = $1
        """
        params = [enabled_only]
        
        if tenant_id:
            query += " AND (tenant_id = $2 OR tenant_id IS NULL)"
            params.append(tenant_id)
        else:
            query += " AND tenant_id IS NULL"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        # Parse JSON fields
        results = []
        for row in rows:
            row_dict = dict(row)
            # Parse keywords from JSON string if needed
            if row_dict.get("keywords"):
                if isinstance(row_dict["keywords"], str):
                    row_dict["keywords"] = json.loads(row_dict["keywords"])
                # If it's already a dict (JSONB), keep it as is
            else:
                row_dict["keywords"] = {}
            
            # Parse scope_filter from JSON string if needed
            if row_dict.get("scope_filter"):
                if isinstance(row_dict["scope_filter"], str):
                    row_dict["scope_filter"] = json.loads(row_dict["scope_filter"])
            else:
                row_dict["scope_filter"] = None
            
            results.append(row_dict)
        
        return results
    
    async def get_routing_rules(
        self,
        tenant_id: Optional[UUID] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get routing rules for tenant (or global)"""
        pool = database_client.pool
        
        query = """
            SELECT 
                id, tenant_id, rule_name, enabled, intent_pattern,
                target_domain, target_agent, target_workflow,
                priority, fallback_chain, scope, scope_filter,
                description, created_by, created_at, updated_at, version
            FROM routing_rules
            WHERE enabled = $1
        """
        params = [enabled_only]
        
        if tenant_id:
            query += " AND (tenant_id = $2 OR tenant_id IS NULL)"
            params.append(tenant_id)
        else:
            query += " AND tenant_id IS NULL"
        
        query += " ORDER BY priority DESC, created_at ASC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def get_prompt_templates(
        self,
        tenant_id: Optional[UUID] = None,
        template_type: Optional[str] = None,
        domain: Optional[str] = None,
        agent: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get prompt templates"""
        pool = database_client.pool
        
        query = """
            SELECT 
                id, tenant_id, template_name, template_type, domain, agent,
                enabled, template_text, variables, version, is_active,
                description, created_by, created_at, updated_at
            FROM prompt_templates
            WHERE enabled = true
        """
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
        
        query += " ORDER BY domain NULLS LAST, agent NULLS LAST, template_name"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def get_tool_permissions(
        self,
        tenant_id: Optional[UUID] = None,
        agent_name: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get tool permissions"""
        pool = database_client.pool
        
        query = """
            SELECT 
                id, tenant_id, agent_name, tool_name, enabled,
                allowed_contexts, rate_limit, required_params,
                description, created_by, created_at, updated_at
            FROM tool_permissions
            WHERE enabled = $1
        """
        params = [enabled_only]
        param_idx = 2
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if agent_name:
            query += f" AND agent_name = ${param_idx}"
            params.append(agent_name)
            param_idx += 1
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def get_guardrails(
        self,
        tenant_id: Optional[UUID] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get guardrails"""
        pool = database_client.pool
        
        query = """
            SELECT 
                id, tenant_id, rule_name, rule_type, enabled,
                trigger_condition, action, action_params,
                priority, scope, scope_filter, description,
                created_by, created_at, updated_at
            FROM guardrails
            WHERE enabled = $1
        """
        params = [enabled_only]
        param_idx = 2
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if rule_type:
            query += f" AND rule_type = ${param_idx}"
            params.append(rule_type)
            param_idx += 1
        
        query += " ORDER BY priority DESC, created_at ASC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]


# Global repository instance
config_repository = ConfigRepository()

