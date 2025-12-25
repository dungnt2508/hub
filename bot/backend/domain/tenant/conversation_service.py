"""
Conversation Service - Manage user_keys, conversations, and conversation_messages
Priority 2: Implement conversation persistence
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json

from backend.shared.logger import logger
from backend.schemas.multi_tenant_types import Conversation, ConversationMessage


class ConversationService:
    """
    Service for managing conversations and messages in PostgreSQL.
    
    Responsibilities:
    - Create/update user_keys
    - Create/update conversations
    - Create conversation_messages
    """
    
    def __init__(self, db_connection):
        """
        Initialize conversation service.
        
        Args:
            db_connection: PostgreSQL connection (from pool)
        """
        self.db = db_connection
    
    async def ensure_user_key(
        self,
        tenant_id: str,
        channel: str,
        user_key: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_display_name: Optional[str] = None,
    ) -> bool:
        """
        Ensure user_key exists in database (create if not exists).
        
        Args:
            tenant_id: Tenant UUID
            channel: Channel ('web', 'telegram', 'teams')
            user_key: User key identifier
            user_id: Optional user identifier (progressive identity)
            user_email: Optional user email (progressive identity)
            user_display_name: Optional user display name (progressive identity)
        
        Returns:
            True if created/updated successfully
        """
        try:
            query = """
            INSERT INTO user_keys (
                id, tenant_id, channel, user_key,
                user_id, user_email, user_display_name,
                first_seen, last_seen
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (tenant_id, channel, user_key) 
            DO UPDATE SET
                last_seen = EXCLUDED.last_seen,
                user_id = COALESCE(EXCLUDED.user_id, user_keys.user_id),
                user_email = COALESCE(EXCLUDED.user_email, user_keys.user_email),
                user_display_name = COALESCE(EXCLUDED.user_display_name, user_keys.user_display_name)
            """
            
            user_key_id = str(uuid.uuid4())
            now = datetime.now()
            
            await self.db.execute(
                query,
                user_key_id,
                tenant_id,
                channel,
                user_key,
                user_id,
                user_email,
                user_display_name,
                now,  # first_seen (only used on INSERT, not updated on conflict)
                now,  # last_seen (updated on conflict)
            )
            
            logger.debug(
                f"User key ensured - tenant: {tenant_id}, channel: {channel}, user_key: {user_key[:8]}..."
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure user_key: {e}", exc_info=True)
            return False
    
    async def get_or_create_conversation(
        self,
        tenant_id: str,
        channel: str,
        user_key: str,
    ) -> Optional[str]:
        """
        Get or create conversation for tenant+channel+user_key.
        
        Uses ON CONFLICT to handle race conditions safely.
        
        Args:
            tenant_id: Tenant UUID
            channel: Channel ('web', 'telegram', 'teams')
            user_key: User key identifier
        
        Returns:
            Conversation ID (UUID string) or None if failed
        """
        try:
            # Try to get existing conversation first (faster path)
            get_query = """
            SELECT id FROM conversations
            WHERE tenant_id = $1 AND channel = $2 AND user_key = $3
            LIMIT 1
            """
            
            row = await self.db.fetchrow(get_query, tenant_id, channel, user_key)
            
            if row:
                conversation_id = str(row['id'])
                logger.debug(f"Found existing conversation: {conversation_id}")
                return conversation_id
            
            # Create new conversation (will fail gracefully if race condition)
            conversation_id = str(uuid.uuid4())
            now = datetime.now()
            
            try:
                create_query = """
                INSERT INTO conversations (
                    id, tenant_id, channel, user_key,
                    message_count, last_message_at, context_data,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                
                await self.db.execute(
                    create_query,
                    conversation_id,
                    tenant_id,
                    channel,
                    user_key,
                    0,  # message_count
                    None,  # last_message_at (no messages yet)
                    json.dumps({}),  # context_data (empty JSON)
                    now,
                    now,
                )
                
                logger.info(
                    f"Created new conversation - tenant: {tenant_id}, "
                    f"channel: {channel}, user_key: {user_key[:8]}..., id: {conversation_id}"
                )
                return conversation_id
                
            except Exception as insert_error:
                # If insert failed (likely unique constraint violation from race condition),
                # try to get again
                logger.debug(f"Conversation insert failed, retrying get: {insert_error}")
                row = await self.db.fetchrow(get_query, tenant_id, channel, user_key)
                if row:
                    return str(row['id'])
                # If still not found, re-raise the original error
                raise insert_error
            
        except Exception as e:
            logger.error(f"Failed to get or create conversation: {e}", exc_info=True)
            return None
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add message to conversation.
        
        Args:
            conversation_id: Conversation UUID
            role: Message role ('user' or 'assistant')
            content: Message content
            intent: Optional intent
            confidence: Optional confidence score
            metadata: Optional metadata dict
        
        Returns:
            True if added successfully
        """
        try:
            message_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Serialize metadata to JSON
            metadata_json = json.dumps(metadata) if metadata else None
            
            insert_query = """
            INSERT INTO conversation_messages (
                id, conversation_id, role, content,
                intent, confidence, metadata, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            
            await self.db.execute(
                insert_query,
                message_id,
                conversation_id,
                role,
                content,
                intent,
                confidence,
                metadata_json,
                now,
            )
            
            # Update conversation stats
            update_query = """
            UPDATE conversations
            SET 
                message_count = message_count + 1,
                last_message_at = $1,
                updated_at = $1
            WHERE id = $2
            """
            
            await self.db.execute(update_query, now, conversation_id)
            
            logger.debug(
                f"Added message to conversation {conversation_id} - role: {role}, "
                f"intent: {intent}, content_length: {len(content)}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}", exc_info=True)
            return False
    
    async def save_conversation_context(
        self,
        conversation_id: str,
        context_data: Dict[str, Any],
    ) -> bool:
        """
        Update conversation context_data.
        
        Args:
            conversation_id: Conversation UUID
            context_data: Context data dict
        
        Returns:
            True if updated successfully
        """
        try:
            query = """
            UPDATE conversations
            SET context_data = $1, updated_at = $2
            WHERE id = $3
            """
            
            metadata_json = json.dumps(context_data)
            await self.db.execute(query, metadata_json, datetime.now(), conversation_id)
            
            logger.debug(f"Updated conversation context: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update conversation context: {e}", exc_info=True)
            return False

