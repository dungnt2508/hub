"""
STEP 0.5: Normalize Input (BẮT BUỘC)
"""
import re
import unicodedata
from datetime import datetime, timedelta

from ...schemas import NormalizedInput, SessionState
from ...shared.exceptions import InvalidInputError
from ...shared.logger import logger


class NormalizeStep:
    """
    Normalize input without inferring intent or domain.
    
    This step only performs text normalization:
    - Trim whitespace
    - Lower-case (except entities)
    - Remove emoji/noise
    - Normalize unicode
    - Expand dates/times
    - Expand common abbreviations
    
    RULES:
    - NO intent inference
    - NO domain injection
    - NO session state modification
    - NO semantic rewriting
    """
    
    def __init__(self):
        # Common Vietnamese abbreviations
        self.abbreviations = {
            "ko": "không",
            "k": "không",
            "dc": "được",
            "vs": "với",
            "mk": "mật khẩu",
            "tk": "tài khoản",
        }
    
    async def execute(
        self,
        raw_message: str,
        session_state: SessionState
    ) -> NormalizedInput:
        """
        Normalize input message.
        
        Args:
            raw_message: Raw user input
            session_state: Current session state (for context only)
            
        Returns:
            NormalizedInput object
            
        Raises:
            InvalidInputError: If input is invalid
        """
        if not raw_message or not raw_message.strip():
            raise InvalidInputError("raw_message is required and non-empty")
        
        # Step 1: Trim whitespace
        normalized = raw_message.strip()
        
        # Step 2: Remove emoji and special characters
        normalized = self._remove_emoji(normalized)
        
        # Step 3: Normalize unicode
        normalized = unicodedata.normalize("NFC", normalized)
        
        # Step 4: Lower-case (preserve entities later)
        normalized_lower = normalized.lower()
        
        # Step 5: Expand abbreviations
        normalized_lower = self._expand_abbreviations(normalized_lower)
        
        # Step 6: Extract and normalize dates
        dates = self._extract_dates(normalized_lower)
        
        # Step 7: Calculate noise level
        noise_level = self._calculate_noise_level(raw_message, normalized_lower)
        
        return NormalizedInput(
            normalized_message=normalized_lower,
            normalized_entities={
                "dates": dates,
            },
            language="vi",
            noise_level=noise_level,
        )
    
    def _remove_emoji(self, text: str) -> str:
        """Remove emoji and special characters"""
        # Remove emoji
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub("", text)
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common Vietnamese abbreviations"""
        words = text.split()
        expanded = []
        for word in words:
            expanded.append(self.abbreviations.get(word, word))
        return " ".join(expanded)
    
    def _extract_dates(self, text: str) -> list[dict]:
        """Extract and normalize dates"""
        dates = []
        today = datetime.now().date()
        
        # Pattern: "mai" -> tomorrow
        if "mai" in text:
            tomorrow = today + timedelta(days=1)
            dates.append({
                "raw": "mai",
                "value": tomorrow.isoformat(),
                "confidence": 0.9,
            })
        
        # Pattern: "hôm nay" -> today
        if "hôm nay" in text:
            dates.append({
                "raw": "hôm nay",
                "value": today.isoformat(),
                "confidence": 0.9,
            })
        
        # TODO: Add more date patterns
        
        return dates
    
    def _calculate_noise_level(self, original: str, normalized: str) -> str:
        """Calculate noise level"""
        if len(original) == len(normalized):
            return "LOW"
        elif abs(len(original) - len(normalized)) < len(original) * 0.1:
            return "MEDIUM"
        else:
            return "HIGH"

