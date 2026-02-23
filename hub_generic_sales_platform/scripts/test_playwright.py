import asyncio
import sys
import os
import json
from playwright.async_api import async_playwright
sys.path.append(os.getcwd())

# Force UTF-8 encoding for Windows terminal output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.core.services.scraping_service import ScrapingService
from app.core.services.ai_parser_service import AIParserService

async def run_detailed_test(url: str):
    print(f"\n--- STARTING PRODUCT EXTRACTION TEST ---")
    print(f"URL: {url}")
    
    scraper = ScrapingService()
    parser = AIParserService()
    
    # 1. Scrape using ScrapingService (Singleton Playwright)
    print("\n1. [SCRAPING] Fetching text content...")
    try:
        raw_text = await scraper.scrape_url(url)
        if not raw_text:
            print("FAILED: No text content returned.")
            return
        print(f"DONE: Got {len(raw_text)} characters.")
    except Exception as e:
        print(f"FAILED: {e}")
        return

    # 2. Manual Extraction using Playwright (Detailed View)
    print("\n2. [CSS EXTRACTION] Fetching specific elements...")
    try:
        browser = await scraper._get_browser()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # PNJ Selectors (Updated Attempt)
        selectors = {
            "name": "h1, .product-detail-name, #product-name",
            "price": ".price, .product-price, .product-detail-price",
            "sku": ".sku, .product-code, .product-sku",
            "attributes": "table, .product-config, .product-details-content"
        }
        
        print("\n--- HTML DIAGNOSTICS ---")
        # Print all class names on the page to find clues
        classes = await page.evaluate("() => Array.from(new Set(Array.from(document.querySelectorAll('*')).flatMap(el => Array.from(el.classList))))")
        print(f"Top classes found: {classes[:20]}")
        
        extracted = {}
        for key, selector in selectors.items():
            if key == "attributes":
                rows = await page.query_selector_all(selector)
                attrs = {}
                for row in rows:
                    cells = await row.query_selector_all("td")
                    if len(cells) >= 2:
                        k = await cells[0].inner_text()
                        v = await cells[1].inner_text()
                        attrs[k.strip()] = v.strip()
                extracted[key] = attrs
            else:
                el = await page.query_selector(selector)
                extracted[key] = (await el.inner_text()).strip() if el else "Not Found"
        
        print(json.dumps(extracted, indent=2, ensure_ascii=False))
        await page.close()
    except Exception as e:
        print(f"CSS Extraction Error: {e}")

    # 3. AI Extraction
    print("\n3. [AI EXTRACTION] Parsing with LLM...")
    try:
        # Simulate some attribute definitions to guide the AI
        from app.core.domain.knowledge import DomainAttributeDefinition, AttributeValueType
        mock_defs = [
            DomainAttributeDefinition(id="1", domain_id="pnj", key="Chất liệu", value_type=AttributeValueType.TEXT),
            DomainAttributeDefinition(id="2", domain_id="pnj", key="Loại đá", value_type=AttributeValueType.TEXT),
            DomainAttributeDefinition(id="3", domain_id="pnj", key="Màu sắc", value_type=AttributeValueType.TEXT),
            DomainAttributeDefinition(id="4", domain_id="pnj", key="Trọng lượng", value_type=AttributeValueType.TEXT)
        ]
        
        ai_result = await parser.parse_product_data(raw_text, attr_definitions=mock_defs)
        print("AI Result:")
        print(json.dumps(ai_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"AI Extraction Error: {e}")

if __name__ == "__main__":
    url = "https://www.pnj.com.vn/omni-trang-suc-xuan-than-tai-2026?atm_source=homepage&atm_medium=bantimgihomnay&atm_campaign=slide1&atm_content="
    asyncio.run(run_detailed_test(url))
