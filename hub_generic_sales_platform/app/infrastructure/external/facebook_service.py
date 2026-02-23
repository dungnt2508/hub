import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FacebookService:
    """
    Service to interact with Facebook Messenger Platform (Graph API).
    """
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self):
        pass

    async def send_message(
        self, 
        page_access_token: str, 
        recipient_id: str, 
        text: str
    ) -> Dict[str, Any]:
        """
        Gửi tin nhắn phản hồi qua Messenger.
        """
        url = f"{self.BASE_URL}/me/messages"
        
        params = {
            "access_token": page_access_token
        }
        
        payload = {
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": text
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, json=payload) as response:
                    data = await response.json()
                    
                    if "error" in data:
                        logger.error(f"[FB] Send failed: {data['error']}")
                        return {"success": False, "error": data["error"]}
                    
                    logger.info(f"[FB] Sent to {recipient_id}: {text[:20]}...")
                    return {"success": True, "data": data}
                    
        except Exception as e:
            logger.error(f"[FB] Exception: {str(e)}")
            return {"success": False, "error": str(e)}
