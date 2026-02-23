import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Thread pool riêng cho Playwright (tránh conflict với event loop chính trên Windows)
_playwright_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="playwright")


def _scrape_url_sync(url: str) -> Optional[str]:
    """
    Chạy scraping trong thread riêng với event loop mới.
    Khắc phục NotImplementedError (subprocess) khi Playwright chạy trong event loop
    của FastAPI/uvicorn trên Windows.
    """
    import asyncio
    from playwright.async_api import async_playwright

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async def _do_scrape() -> Optional[str]:
        playwright = None
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            try:
                logger.info(f"Scraping URL: {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                content = await page.evaluate("() => document.body.innerText")
                return content[:15000] if content else None
            finally:
                await page.close()
                await context.close()
            await browser.close()
        finally:
            if playwright:
                await playwright.stop()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_do_scrape())
    finally:
        loop.close()


class ScrapingService:
    """
    Handles robust web scraping using Playwright.
    Supports dynamic content rendering (JS) and basic content cleaning.
    Chạy trong thread riêng trên Windows để tránh NotImplementedError (subprocess).
    """

    async def scrape_url(self, url: str) -> Optional[str]:
        """
        Navigates to the URL and returns the cleaned text content.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(_playwright_executor, _scrape_url_sync, url)
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise e

    @classmethod
    async def close(cls):
        """Shutdown executor khi cần (dùng trong test hoặc shutdown app)"""
        _playwright_executor.shutdown(wait=False)
