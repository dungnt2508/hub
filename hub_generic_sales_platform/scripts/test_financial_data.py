import asyncio
import httpx
import time
import json
import sys

# --- CONFIGURATION ---
TICKER = "VIC"
TIMEOUT = 10.0
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://iboard.ssi.com.vn/"
}

async def fetch_api(name, url, headers=None):
    print(f"\n[Testing {name}]")
    print(f"URL: {url}")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers or HEADERS)
            duration = time.time() - start
            print(f"Status: {resp.status_code} (in {duration:.2f}s)")
            if resp.status_code == 200:
                data = resp.json()
                print("Data Received!")
                return data
            else:
                print(f"Error Body: {resp.text[:100]}")
    except httpx.ConnectTimeout:
        print(f"FAILED: Connection Timeout after {TIMEOUT}s. (Có thể do tường lửa hoặc chặn IP)")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)}")
    return None

async def main():
    print("====================================================")
    print("   IRIS HUB - FINANCIAL API DIAGNOSTIC TOOL v2.0")
    print("====================================================")
    print(f"Local Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Stock: {TICKER}")
    
    # 1. Test SSI iBoard
    ssi_url = f"https://iboardquery.ssi.com.vn/stock/stock-data?stocks={TICKER}"
    ssi_data = await fetch_api("SSI iBoard", ssi_url)

    # 2. Test VNDirect
    vdirect_url = f"https://finfo-api.vndirect.com.vn/v4/stock_prices?filter=symbol:{TICKER}"
    vnd_data = await fetch_api("VNDirect Finfo", vdirect_url)

    # 3. Test VNAppMob Gold
    gold_url = "https://api.vnappmob.com/api/v2/gold/sjc"
    # Note: Requires API Key if strictly enforced, testing public access
    gold_data = await fetch_api("VNAppMob Gold", gold_url)

    print("\n" + "="*50)
    print("   SUMMARY & RECOMMENDATION")
    print("="*50)
    
    if not ssi_data and not vnd_data:
        print("[-] CẢNH BÁO: Không thể kết nối đến bất kỳ sàn chứng khoán nào.")
        print("    Nguyên nhân có thể do:")
        print("    1. Môi trường sandbox/server của bạn đang chặn các domain tài chính.")
        print("    2. IP của bạn đang bị nhà cung cấp dữ liệu chặn (Rate Limit).")
        print("    HÀNH ĐỘNG: Hãy thử chạy file này trên máy cá nhân hoặc máy chủ tại Việt Nam.")
    else:
        print("[+] THÀNH CÔNG: Đã kết nối được với ít nhất một nguồn dữ liệu.")

    if not gold_data:
        print("[-] CẢNH BÁO: Giá vàng yêu cầu API Key hoặc bị chặn truy cập công khai.")

    print("\n[Mô phỏng Phản hồi IRIS Bot]:")
    print("-" * 30)
    if ssi_data and 'data' in ssi_data and ssi_data['data']:
        s = ssi_data['data'][0]
        print(f"Bot: Giá cổ phiếu {TICKER} hiện tại là {s.get('l')} nghìn VNĐ/CP.")
    else:
        print(f"Bot: Hiện tại tôi không thể lấy giá trực tiếp của {TICKER} do gián đoạn kết nối sàn HOSE.")
        print("     Dưới đây là giá tham chiếu gần nhất: 43.5 nghìn VNĐ/CP.")
    
    print("\n--- TEST COMPLETED ---")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
