"""
STEP 2: Global Pattern Match (Hard Rule)
"""
import re
from typing import Dict, Any, Optional
from uuid import UUID

from ...shared.logger import logger
from ...shared.exceptions import PatternMatchError, ExternalServiceError
from ...infrastructure.config_loader import config_loader
from ...shared.config_cache import get_config_cache


class PatternMatchStep:
    """
    Deterministic pattern matching with priority-based rules.
    
    This step provides high-confidence routing decisions.
    Loads patterns from cache (ConfigCache handles DB loading and caching).
    
    NOTE: Internal caching has been REMOVED. Use ConfigCache for caching.
    """
    
    def __init__(self):
        self._compiled_patterns_cache: Dict[str, list] = {}  # tenant_id -> compiled patterns
        self.config_cache = get_config_cache()
    
    async def _compile_patterns(self, rules: list) -> list:
        """
        Compile regex patterns from rules.
        
        Raises:
            PatternMatchError: If pattern compilation fails
        """
        compiled = []
        for rule in rules:
            try:
                # Parse regex flags
                flags = 0
                if rule.get("pattern_flags"):
                    flag_str = rule["pattern_flags"].upper()
                    if "IGNORECASE" in flag_str or "I" in flag_str:
                        flags |= re.IGNORECASE
                    if "MULTILINE" in flag_str or "M" in flag_str:
                        flags |= re.MULTILINE
                    if "DOTALL" in flag_str or "S" in flag_str:
                        flags |= re.DOTALL
                
                pattern = re.compile(rule["pattern_regex"], flags)
                compiled.append((
                    pattern,
                    rule["target_domain"],
                    rule.get("target_intent"),
                    rule.get("intent_type"),
                    rule.get("priority", 0),
                    rule.get("slots_extraction", {}),
                    rule.get("id"),  # For logging
                ))
            except re.error as e:
                # Invalid regex pattern - log warning but continue
                logger.warning(
                    f"Failed to compile pattern rule {rule.get('id')}: {e}",
                    extra={"rule_id": rule.get("id"), "pattern": rule.get("pattern_regex")}
                )
                continue
            except Exception as e:
                # Unexpected error compiling pattern - raise
                logger.error(
                    f"Unexpected error compiling pattern rule {rule.get('id')}: {e}",
                    extra={"rule_id": rule.get("id"), "pattern": rule.get("pattern_regex")},
                    exc_info=True
                )
                raise PatternMatchError(f"Failed to compile pattern rule: {e}") from e
        
        # Sort by priority (descending)
        compiled.sort(key=lambda x: x[4], reverse=True)
        return compiled
    
    def _extract_slots(self, message: str, pattern: re.Pattern, slots_extraction: Dict[str, str]) -> Dict[str, Any]:
        """Extract slots from matched pattern"""
        if not slots_extraction:
            return {}
        
        match = pattern.search(message)
        if not match:
            return {}
        
        slots = {}
        for slot_name, group_ref in slots_extraction.items():
            try:
                # Support both group index (0, 1, 2) and group name
                if group_ref.isdigit():
                    group_idx = int(group_ref)
                    if group_idx < len(match.groups()) + 1:  # +1 for full match
                        slots[slot_name] = match.group(group_idx)
                else:
                    # Try as named group
                    if match.lastgroup:
                        slots[slot_name] = match.group(group_ref)
            except (IndexError, KeyError):
                continue
        
        return slots
    
    async def execute(self, message: str, tenant_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Match message against patterns.
        
        Args:
            message: Normalized message
            tenant_id: Optional tenant ID for tenant-specific patterns
            
        Returns:
            Dict with "matched" flag and routing info if matched
        """
        try:
            # Load patterns from cache (ConfigCache handles caching)
            rules = await self.config_cache.get_pattern_rules(
                tenant_id,
                lambda tid: config_loader.get_pattern_rules(tid, enabled_only=True)
            )
            
            if not rules:
                return {"matched": False}
            
            # Compile patterns (this is lightweight, can be cached in memory if needed)
            tenant_key = str(tenant_id) if tenant_id else "global"
            if tenant_key not in self._compiled_patterns_cache:
                self._compiled_patterns_cache[tenant_key] = await self._compile_patterns(rules)
            
            compiled_patterns = self._compiled_patterns_cache[tenant_key]
            
            if not compiled_patterns:
                return {"matched": False}
            
            # Match against patterns
            for pattern, domain, intent, intent_type, priority, slots_extraction, rule_id in compiled_patterns:
                if pattern.search(message):
                    slots = self._extract_slots(message, pattern, slots_extraction)
                    
                    logger.info(
                        "Pattern matched",
                        extra={
                            "pattern": pattern.pattern,
                            "domain": domain,
                            "intent": intent,
                            "rule_id": str(rule_id) if rule_id else None,
                            "priority": priority,
                        }
                    )
                    
                    return {
                        "matched": True,
                        "domain": domain,
                        "intent": intent,
                        "intent_type": intent_type,
                        "slots": slots,
                        "confidence": 1.0,
                        "source": "PATTERN",
                    }
            
            return {"matched": False}
            
        except Exception as e:
            logger.error(
                f"Pattern matching failed: {e}",
                extra={"tenant_id": str(tenant_id) if tenant_id else None},
                exc_info=True
            )
            raise

