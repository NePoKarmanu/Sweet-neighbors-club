from __future__ import annotations

from dataclasses import dataclass, field
import logging

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.listing_cache import invalidate_listing_list_cache
from backend.db.repositories.aggregators import AggregatorRepository
from backend.db.repositories.listings import ListingRepository
from backend.logging_utils import log_exception, log_info
from backend.scrapers.registry import load_scrapers

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScraperRunError:
    aggregator_name: str
    message: str


@dataclass(frozen=True)
class ScrapeRunResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    requested_provider: str | None = None
    executed_providers: list[str] = field(default_factory=list)
    errors: list[ScraperRunError] = field(default_factory=list)


def run_all_scrapers(
    db: Session,
    provider_name: str | None = None,
) -> ScrapeRunResult:
    log_info(logger, "Scraping run started", event="scraping.run_started", provider_name=provider_name)
    created = 0
    updated = 0
    has_successful_upsert = False
    executed_providers: list[str] = []
    errors: list[ScraperRunError] = []

    aggregator_repository = AggregatorRepository(db)
    listing_repository = ListingRepository(db)

    for scraper in load_scrapers(provider_name=provider_name):
        executed_providers.append(scraper.aggregator_name)
        log_info(
            logger, "Scraper provider started", event="scraping.provider_started",
            provider_name=scraper.aggregator_name
        )
        try:
            aggregator = aggregator_repository.get_or_create(
                name=scraper.aggregator_name,
                base_url=scraper.base_url,
            )
            scraped_listings = scraper.scrape()
            payloads = [listing.to_repository_payload() for listing in scraped_listings]
            result = listing_repository.upsert_many(
                aggregator_id=aggregator.id,
                listings=payloads,
                stale_misses_threshold=settings.SCRAPER_STALE_MISSES_THRESHOLD,
            )
            has_successful_upsert = True
            created += result.created
            updated += result.updated
            log_info(
                logger, "Scraper provider finished", event="scraping.provider_finished",
                provider_name=scraper.aggregator_name, created=result.created, updated=result.updated
            )
        except Exception as exc:
            log_exception(
                logger, "Scraper provider failed", event="scraping.provider_failed",
                provider_name=scraper.aggregator_name
            )
            db.rollback()
            errors.append(
                ScraperRunError(
                    aggregator_name=scraper.aggregator_name,
                    message=str(exc),
                )
            )

    if has_successful_upsert:
        invalidate_listing_list_cache()
        log_info(
            logger, "Listings cache invalidated after scraping upsert",
            event="scraping.cache_invalidated", provider_name=provider_name
        )

    result = ScrapeRunResult(
        created=created,
        updated=updated,
        failed=len(errors),
        requested_provider=provider_name,
        executed_providers=executed_providers,
        errors=errors,
    )
    log_info(
        logger, "Scraping run finished", event="scraping.run_finished", provider_name=provider_name,
        created=result.created, updated=result.updated, failed=result.failed, executed_providers=result.executed_providers
    )
    return result
