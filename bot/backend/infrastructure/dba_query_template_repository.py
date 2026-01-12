"""
DBA Query Template Repository - Database queries for DBA query templates
"""
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..shared.logger import logger
from .database_client import database_client


class DBAQueryTemplateRepository:
    """Repository for DBA query template database queries"""
    
    async def get_templates_by_playbook(
        self,
        playbook_name: str,
        db_type: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get query templates for a playbook and database type.
        
        Args:
            playbook_name: Playbook name (e.g., "QUERY_PERFORMANCE")
            db_type: Database type (e.g., "sqlserver", "postgresql", "mysql")
            active_only: Only return active versions
            
        Returns:
            List of query templates ordered by step_number
        """
        pool = database_client.pool
        
        query = """
            SELECT 
                id, playbook_name, db_type, step_number, purpose,
                query_text, read_only, version, is_active,
                description, created_by, created_at, updated_at
            FROM dba_query_templates
            WHERE playbook_name = $1
                AND db_type = $2
        """
        params = [playbook_name, db_type]
        
        if active_only:
            query += " AND is_active = $3"
            params.append(True)
        
        query += " ORDER BY step_number ASC, version DESC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        # If active_only, filter to get only latest active version per step
        result = [dict(row) for row in rows]
        if active_only:
            # Group by step_number and take latest version
            steps = {}
            for template in result:
                step_num = template['step_number']
                if step_num not in steps or template['version'] > steps[step_num]['version']:
                    steps[step_num] = template
            result = list(steps.values())
            result.sort(key=lambda x: x['step_number'])
        
        return result
    
    async def get_all_templates(
        self,
        playbook_name: Optional[str] = None,
        db_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all query templates with optional filters.
        
        Args:
            playbook_name: Optional filter by playbook name
            db_type: Optional filter by database type
            active_only: Only return active versions
            
        Returns:
            List of query templates
        """
        pool = database_client.pool
        
        query = """
            SELECT 
                id, playbook_name, db_type, step_number, purpose,
                query_text, read_only, version, is_active,
                description, created_by, created_at, updated_at
            FROM dba_query_templates
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if playbook_name:
            query += f" AND playbook_name = ${param_idx}"
            params.append(playbook_name)
            param_idx += 1
        
        if db_type:
            query += f" AND db_type = ${param_idx}"
            params.append(db_type)
            param_idx += 1
        
        if active_only:
            query += f" AND is_active = ${param_idx}"
            params.append(True)
            param_idx += 1
        
        query += " ORDER BY playbook_name, db_type, step_number ASC, version DESC"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def create_template(
        self,
        playbook_name: str,
        db_type: str,
        step_number: int,
        purpose: str,
        query_text: str,
        read_only: bool = True,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a new query template.
        
        Returns:
            Created template dict
        """
        pool = database_client.pool
        
        query = """
            INSERT INTO dba_query_templates
                (playbook_name, db_type, step_number, purpose, query_text,
                 read_only, description, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING 
                id, playbook_name, db_type, step_number, purpose,
                query_text, read_only, version, is_active,
                description, created_by, created_at, updated_at
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                playbook_name, db_type, step_number, purpose,
                query_text, read_only, description, created_by
            )
        
        return dict(row) if row else {}
    
    async def update_template(
        self,
        template_id: UUID,
        query_text: Optional[str] = None,
        purpose: Optional[str] = None,
        description: Optional[str] = None,
        read_only: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a query template (creates new version).
        
        Returns:
            Updated template dict or None if not found
        """
        pool = database_client.pool
        
        # Get current template
        get_query = "SELECT * FROM dba_query_templates WHERE id = $1 AND is_active = true"
        async with pool.acquire() as conn:
            current = await conn.fetchrow(get_query, template_id)
            
            if not current:
                return None
            
            # Deactivate old version
            await conn.execute(
                "UPDATE dba_query_templates SET is_active = false WHERE id = $1",
                template_id
            )
            
            # Create new version
            new_query = """
                INSERT INTO dba_query_templates
                    (playbook_name, db_type, step_number, purpose, query_text,
                     read_only, description, version, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING 
                    id, playbook_name, db_type, step_number, purpose,
                    query_text, read_only, version, is_active,
                    description, created_by, created_at, updated_at
            """
            
            new_purpose = purpose if purpose is not None else current['purpose']
            new_query_text = query_text if query_text is not None else current['query_text']
            new_description = description if description is not None else current['description']
            new_read_only = read_only if read_only is not None else current['read_only']
            new_version = current['version'] + 1
            
            row = await conn.fetchrow(
                new_query,
                current['playbook_name'],
                current['db_type'],
                current['step_number'],
                new_purpose,
                new_query_text,
                new_read_only,
                new_description,
                new_version,
                current['created_by']
            )
        
        return dict(row) if row else None


# Global repository instance
dba_query_template_repository = DBAQueryTemplateRepository()

