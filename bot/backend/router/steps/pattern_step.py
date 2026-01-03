"""
STEP 2: Global Pattern Match (Hard Rule)
"""
import re
from typing import Dict, Any, Optional
from uuid import UUID

from ...shared.logger import logger
from ...infrastructure.config_loader import config_loader


class PatternMatchStep:
    """
    Deterministic pattern matching with priority-based rules.
    
    This step provides high-confidence routing decisions.
    Loads patterns from database via config_loader.
    """
    
    def __init__(self):
        self._compiled_patterns: Optional[list] = None
        self._last_tenant_id: Optional[UUID] = None
        self._last_refresh_time: float = 0
        self._refresh_interval = 300  # 5 minutes
    
    async def _load_patterns(self, tenant_id: Optional[UUID] = None):
        """Load and compile patterns from config"""
        import time
        
        current_time = time.time()
        
        # Check if we need to refresh (different tenant or expired)
        if (
            self._compiled_patterns is None
            or tenant_id != self._last_tenant_id
            or (current_time - self._last_refresh_time) > self._refresh_interval
        ):
            # Load from config loader
            rules = await config_loader.get_pattern_rules(tenant_id, enabled_only=True)
            
            # Compile patterns
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
                except Exception as e:
                    logger.warning(
                        f"Failed to compile pattern rule {rule.get('id')}: {e}",
                        extra={"rule_id": rule.get("id"), "pattern": rule.get("pattern_regex")}
                    )
                    continue
            
            # Sort by priority (descending)
            compiled.sort(key=lambda x: x[4], reverse=True)
            
            self._compiled_patterns = compiled
            self._last_tenant_id = tenant_id
            self._last_refresh_time = current_time
    
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
        await self._load_patterns(tenant_id)
        
        if not self._compiled_patterns:
            return {"matched": False}
        
        for pattern, domain, intent, intent_type, priority, slots_extraction, rule_id in self._compiled_patterns:
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

