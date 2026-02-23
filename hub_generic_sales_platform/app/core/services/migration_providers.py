from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.knowledge import MigrationJob
from app.core.services.migration_service import BaseMigrationProvider
import asyncio

from app.core.services.scraping_service import ScrapingService
from app.core.services.ai_parser_service import AIParserService
import logging

logger = logging.getLogger(__name__)

class RealWebScraperProvider(BaseMigrationProvider):
    """
    Real AI Scraper using Playwright + LLM.
    """
    
    def __init__(self):
        self.scraper = ScrapingService()
        self.parser = AIParserService()

    async def fetch_and_parse(self, job: MigrationJob, db: AsyncSession) -> Dict[str, Any]:
        url = job.batch_metadata.get("url")
        if not url:
            raise ValueError("URL is required for web scraping")
            
        # 1. Fetch Domain Definitions for extraction guidance
        from app.infrastructure.database.repositories import DomainAttributeDefinitionRepository
        attr_repo = DomainAttributeDefinitionRepository(db)
        attr_defs = []
        if job.domain_id:
            attr_defs = await attr_repo.get_by_domain(job.domain_id)

        # 2. Scrape
        logger.info(f"Starting real scrape for: {url}")
        raw_text = await self.scraper.scrape_url(url)
        if not raw_text:
            raise Exception("Không thể lấy dữ liệu từ URL này.")
            
        # 3. AI Parse with guidance (trả {"offerings": [...]} - thống nhất domain)
        logger.info(f"Starting AI parsing for: {url} (Domain: {job.domain_id})")
        parsed = await self.parser.parse_offering_data(raw_text, attr_definitions=attr_defs)
        offerings = parsed.get("offerings", [])
        return {"offerings": offerings}
