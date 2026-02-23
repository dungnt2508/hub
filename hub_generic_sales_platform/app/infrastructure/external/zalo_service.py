import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ZaloService:
    """
    Service to interact with Zalo Official Account API (v3).
    """
    BASE_URL = "https://openapi.zalo.me/v3.0/oa"

    def __init__(self):
        pass

    async def send_message(
        self, 
        access_token: str, 
        recipient_id: str, 
        text: str,
        attachment_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gửi tin nhắn tư vấn tới người dùng Zalo.
        
        Args:
            access_token: Zalo OA Access Token
            recipient_id: Zalo User ID (from webhook)
            text: Nội dung tin nhắn
            attachment_url: (Optional) Ảnh đính kèm
        """
        url = f"{self.BASE_URL}/message/cs"
        
        headers = {
            "Content-Type": "application/json",
            "access_token": access_token
        }
        
        payload = {
            "recipient": {
                "user_id": recipient_id
            },
            "message": {
                "text": text
            }
        }
        
        if attachment_url:
             payload["message"]["attachment"] = {
                 "type": "template",
                 "payload": {
                     "template_type": "media",
                     "elements": [{
                         "media_type": "image",
                         "url": attachment_url
                     }]
                 }
             }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    
                    if data.get("error") != 0:
                        logger.error(f"[Zalo] Send failed: {data}")
                        return {"success": False, "error": data}
                    
                    logger.info(f"[Zalo] Sent to {recipient_id}: {text[:20]}...")
                    return {"success": True, "data": data}
                    
        except Exception as e:
            logger.error(f"[Zalo] Exception: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_user_profile(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """Lấy thông tin người dùng (tên, avatar)"""
        url = f"{self.BASE_URL}/user/getprofile"
        headers = {"access_token": access_token}
        params = {"data": f'{{"user_id":"{user_id}"}}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    data = await response.json()
                    if data.get("error") != 0:
                        return {}
                    return data.get("data", {})
        except Exception:
            return {}
