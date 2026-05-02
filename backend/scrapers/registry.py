from __future__ import annotations

import importlib
import inspect
import pkgutil

from backend.scrapers import providers
from backend.scrapers.base import ListingScraper, ScraperProviderNotFoundError


def _normalize_provider_name(provider_name: str | None) -> str | None:
    if provider_name is None:
        return None
    normalized = provider_name.strip().lower()
    return normalized or None


def load_scrapers(provider_name: str | None = None) -> list[ListingScraper]:
    scrapers: list[ListingScraper] = []
    requested_provider = _normalize_provider_name(provider_name)
    package_prefix = providers.__name__ + "."

    for module_info in pkgutil.iter_modules(providers.__path__, package_prefix):
        module = importlib.import_module(module_info.name)
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate.__module__ != module.__name__:
                continue
            if candidate.__name__.startswith("_"):
                continue
            if not hasattr(candidate, "aggregator_name") or not hasattr(candidate, "base_url"):
                continue
            if not callable(getattr(candidate, "scrape", None)):
                continue
            scraper = candidate()
            if requested_provider is not None:
                if scraper.aggregator_name.strip().lower() != requested_provider:
                    continue
            scrapers.append(scraper)

    if requested_provider is not None and not scrapers:
        raise ScraperProviderNotFoundError(
            f"Scraper provider '{requested_provider}' is not registered"
        )

    return scrapers


def list_provider_names() -> list[str]:
    return sorted({scraper.aggregator_name for scraper in load_scrapers()})
