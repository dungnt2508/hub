import asyncio
import sys
import os
import json
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Setup path to import app modules
sys.path.append(os.getcwd())

# Force UTF-8 encoding for Windows terminal output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.core.services.scraping_service import ScrapingService
from app.core.services.ai_parser_service import AIParserService

import hashlib

# Mock Database / Semantic Cache for Demo
# Trong ứng dụng thực tế, cái này sẽ query vào bảng `tenant_semantic_cache`
GLOBAL_CACHE = {} 

class SmartScraper:
    def __init__(self):
        self.scraper = ScrapingService()
        self.parser = AIParserService()
        
    async def extract_product(self, url: str, force_ai: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """
        Flow nâng cao:
        1. Fetch HTML.
        2. Dò tìm xem là trang LISTING hay DETAIL (Ưu tiên JSON-LD).
        3. Nếu là DETAIL: Kiểm tra Cache DB -> Nếu lỡ cache thì dùng, không thì AI -> Lưu Cache.
        4. Nếu là LISTING: Bóc tách toàn bộ danh sách.
        """
        print(f"\n[START] Processing: {url}")
        
        browser = await self.scraper._get_browser()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)
            
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            raw_text = await page.evaluate("() => document.body.innerText")
            
            results = {
                "source_url": url,
                "type": "unknown", # detail | listing
                "strategies_used": [],
                "products": [] # Luôn trả về mảng products
            }

            # --- BƯỚC 1: DÒ TÌM LOẠI TRANG (JSON-LD ItemList) ---
            json_ld_raw = self._get_all_json_ld(soup)
            is_listing = False
            for js in json_ld_raw:
                if js.get("@type") == "ItemList" or "itemListElement" in js:
                    is_listing = True
                    break
            
            results["type"] = "listing" if is_listing else "detail"
            print(f"  >> Detected Type: {results['type'].upper()}")

            # --- BƯỚC 2: KIỂM TRA CACHE (Nếu là Detail và không Force AI) ---
            cache_key = self._generate_cache_key(url, raw_text)
            if use_cache and not force_ai and not is_listing:
                cached_data = GLOBAL_CACHE.get(cache_key)
                if cached_data:
                    print(f"  >> [CACHE HIT] Tìm thấy kết quả trong Database Cache!")
                    results["products"] = cached_data
                    results["strategies_used"].append("DB-Cache")
                    return results

            # --- BƯỚC 3: TRÍCH XUẤT DỮ LIỆU ---
            if is_listing:
                # Nếu là trang danh sách, dùng AI để liệt kê hết
                print(f"  >> [AI LISTING] Đang bóc tách danh sách sản phẩm...")
                ai_result = await self.parser.parse_offering_data(raw_text[:15000])
                results["products"] = ai_result.get("offerings", ai_result.get("products", []))
                results["strategies_used"].append("AI-Listing-Extraction")
            else:
                # Nếu là trang chi tiết, thử lấy từ JSON-LD/Meta trước
                detail_data = self._extract_detail_from_soup(soup)
                
                # Nếu thiếu thông tin quan trọng -> Gọi AI
                if force_ai or not detail_data.get("name") or not detail_data.get("price"):
                    print(f"  >> [AI DETAIL] Đang bóc tách chi tiết sâu bằng LLM...")
                    ai_result = await self.parser.parse_offering_data(raw_text[:12000])
                    objs = ai_result.get("offerings", ai_result.get("products", []))
                    if objs:
                        p = objs[0]
                        detail_data.update({
                            "name": p.get("name") or detail_data.get("name"),
                            "sku": p.get("code") or detail_data.get("sku"),
                            "attributes": p.get("attributes", {})
                        })
                        results["strategies_used"].append("AI-Detail-Refinement")
                else:
                    results["strategies_used"].append("JSON-LD/Meta")

                results["products"] = [detail_data]

            # --- BƯỚC 4: LƯU CACHE (Chỉ lưu detail để demo) ---
            if not is_listing and results["products"]:
                print(f"  >> [CACHE SAVE] Lưu kết quả vào Database cho lần sau.")
                GLOBAL_CACHE[cache_key] = results["products"]

            return results
        except Exception as e:
            print(f"  !! [ERROR] {url}: {e}")
            return {"source_url": url, "error": str(e), "products": []}
        finally:
            await page.close()

    def _generate_cache_key(self, url: str, content: str) -> str:
        # Key = hash của URL + 500 ký tự đầu của content để nhận diện thay đổi nội dung
        text_id = f"{url}_{content[:500]}"
        return hashlib.md5(text_id.encode()).hexdigest()

    def _get_all_json_ld(self, soup: BeautifulSoup) -> List[Dict]:
        scripts = soup.find_all('script', type='application/ld+json')
        results = []
        for s in scripts:
            try:
                data = json.loads(s.string)
                if isinstance(data, list): results.extend(data)
                else: results.append(data)
            except: continue
        return results

    def _extract_detail_from_soup(self, soup: BeautifulSoup) -> Dict:
        # Logic cũ: lấy 1 sản phẩm từ JSON-LD hoặc Meta
        data = {"name": None, "sku": None, "price": None}
        all_js = self._get_all_json_ld(soup)
        for js in all_js:
            if js.get("@type") == "Product":
                data["name"] = js.get("name")
                data["sku"] = js.get("sku") or js.get("mpn")
                offers = js.get("offers")
                if offers:
                    if isinstance(offers, list): offers = offers[0]
                    data["price"] = offers.get("price")
                break
        
        # Meta tag fallback
        if not data["name"]:
            meta = soup.find("meta", property="og:title")
            if meta: data["name"] = meta.get("content")
            
        return data

async def main():
    scraper = SmartScraper()
    
    # Mix của trang chi tiết và trang danh sách
    test_urls = [
        "https://www.pnj.com.vn/bong-tai-vang-18k-dinh-da-cz-pnj-xmxmy000511.html", # Detail
        "https://thegioididong.com/dtdd", # Listing page (Danh sách điện thoại)
    ]
    
    print(f"--- ĐANG CHẠY SMART SCRAPER (DETAIL & LISTING) ---")
    
    try:
        # Lần 1: Chưa có cache
        print("\n>>> LẦN CHẠY 1: CHƯA CÓ CACHE")
        tasks = [scraper.extract_product(url) for url in test_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Lần 2: Test Cache (Chỉ chạy lại URL detail)
        print("\n>>> LẦN CHẠY 2: KIỂM TRA DATABASE CACHE")
        await scraper.extract_product(test_urls[0]) # Sẽ thấy CACHE HIT

        # Hiển thị kết quả lần 1 cho đẹp
        print("\n" + "="*50)
        print("TỔNG HỢP KẾT QUẢ")
        for res in results:
            if isinstance(res, Exception): continue
            print(f"- {res.get('source_url')} [{res.get('type')}] -> {len(res.get('products', []))} items")
            if res.get('products'):
                print(f"  Vd sp đầu: {res['products'][0].get('name')}")

    finally:
        print("\n[CLEANUP] Đang đóng browser...")
        await ScrapingService.close()
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
    except RuntimeError as e:
        if "Event loop is closed" not in str(e): raise
