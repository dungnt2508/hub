import asyncio
import aiohttp
import sys
import os

# Create a minimal mock of the environment
sys.path.append(os.getcwd())

async def simulate_zalo_webhook():
    url = "http://localhost:8000/webhooks/zalo/message"
    
    # Mock payload from Zalo
    payload = {
        "event_name": "user_send_text",
        "sender": {
            "id": "zalo_user_123"
        },
        "message": {
            "text": "Chào bot, tôi muốn tìm xe Vios"
        }
    }
    
    headers = {
        "X-Tenant-ID": "default_tenant",
        # "X-Bot-ID": "..." # Optional, let logic find it
    }
    
    print(f"Sending POST to {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
                
                if response.status == 200:
                    print("SUCCESS: Webhook accepted.")
                else:
                    print("FAILURE: Webhook rejected.")
    except Exception as e:
        print(f"Error: {e}")
        print("Ensure the server is running on localhost:8000")

if __name__ == "__main__":
    asyncio.run(simulate_zalo_webhook())
