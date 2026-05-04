from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.repositories.aggregators import AggregatorRepository
from backend.db.repositories.listings import ListingRepository
from backend.scrapers.registry import load_scrapers


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
    created = 0
    updated = 0
    executed_providers: list[str] = []
    errors: list[ScraperRunError] = []

    aggregator_repository = AggregatorRepository(db)
    listing_repository = ListingRepository(db)

    for scraper in load_scrapers(provider_name=provider_name):
        executed_providers.append(scraper.aggregator_name)
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
            created += result.created
            updated += result.updated
        except Exception as exc:
            db.rollback()
            errors.append(
                ScraperRunError(
                    aggregator_name=scraper.aggregator_name,
                    message=str(exc),
                )
            )

    return ScrapeRunResult(
        created=created,
        updated=updated,
        failed=len(errors),
        requested_provider=provider_name,
        executed_providers=executed_providers,
        errors=errors,
    )
