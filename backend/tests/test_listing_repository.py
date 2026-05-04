from __future__ import annotations

import unittest
from datetime import datetime, timezone

from backend.db.models.listings import Listing
from backend.db.repositories.listings import ListingRepository


class _FakeSession:
    def __init__(self, scalars_results: list[list[Listing]]) -> None:
        self._scalars_results = scalars_results
        self._scalars_call_index = 0
        self.added: list[Listing] = []
        self.committed = False

    def scalars(self, _query):
        result = self._scalars_results[self._scalars_call_index]
        self._scalars_call_index += 1
        return result

    def add(self, entity: Listing) -> None:
        self.added.append(entity)

    def commit(self) -> None:
        self.committed = True


class ListingRepositoryTests(unittest.TestCase):
    def test_upsert_many_updates_existing_and_increments_missed(self) -> None:
        existing = Listing(
            aggregator_id=1,
            external_id="seen-1",
            url="https://example.com/seen-1",
            title="Old title",
            missing_runs_count=2,
            deleted_at=datetime.now(timezone.utc),
        )
        stale = Listing(
            aggregator_id=1,
            external_id="stale-1",
            url="https://example.com/stale-1",
            title="Stale title",
            missing_runs_count=1,
        )
        session = _FakeSession([[existing], [stale]])
        repository = ListingRepository(session)  # type: ignore[arg-type]

        result = repository.upsert_many(
            aggregator_id=1,
            listings=[
                {
                    "external_id": "seen-1",
                    "url": "https://example.com/new-seen-1",
                    "title": "New title",
                }
            ],
            stale_misses_threshold=3,
        )

        self.assertEqual(result.created, 0)
        self.assertEqual(result.updated, 1)
        self.assertEqual(existing.url, "https://example.com/new-seen-1")
        self.assertEqual(existing.title, "New title")
        self.assertEqual(existing.missing_runs_count, 0)
        self.assertIsNone(existing.deleted_at)
        self.assertEqual(stale.missing_runs_count, 2)
        self.assertIsNone(stale.deleted_at)
        self.assertTrue(session.committed)

    def test_upsert_many_creates_new_and_marks_stale_as_deleted_on_threshold(self) -> None:
        stale = Listing(
            aggregator_id=1,
            external_id="stale-1",
            url="https://example.com/stale-1",
            title="Stale title",
            missing_runs_count=2,
        )
        session = _FakeSession([[], [stale]])
        repository = ListingRepository(session)  # type: ignore[arg-type]

        result = repository.upsert_many(
            aggregator_id=1,
            listings=[
                {
                    "external_id": "new-1",
                    "url": "https://example.com/new-1",
                    "title": "New listing",
                }
            ],
            stale_misses_threshold=3,
        )

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(len(session.added), 1)
        self.assertEqual(session.added[0].external_id, "new-1")
        self.assertEqual(session.added[0].missing_runs_count, 0)
        self.assertIsNone(session.added[0].deleted_at)
        self.assertEqual(stale.missing_runs_count, 3)
        self.assertIsNotNone(stale.deleted_at)
        self.assertTrue(session.committed)


if __name__ == "__main__":
    unittest.main()
