from __future__ import annotations

from sqlalchemy import Boolean, Integer, cast, func, select
from sqlalchemy.sql import Select

from backend.dto.listings import ListingSearchDTO, ListingSortBy, ListingSortOrder
from backend.db.models.listings import Listing
from backend.db.repositories.base import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    model = Listing

    def _build_ordering(
        self,
        *,
        sort_by: ListingSortBy | None,
        sort_order: ListingSortOrder | None,
    ):
        if sort_by is None or sort_order is None:
            return Listing.published_at.desc().nullslast(), Listing.id.desc()

        if sort_by == "price":
            field = Listing.price
        else:
            field = Listing.published_at

        if sort_order == "asc":
            return field.asc().nullslast(), Listing.id.desc()
        return field.desc().nullslast(), Listing.id.desc()

    def _apply_filters(
        self,
        query: Select[tuple[Listing]],
        search: ListingSearchDTO,
    ) -> Select[tuple[Listing]]:
        query = query.where(Listing.deleted_at.is_(None))

        if search.price is not None:
            if search.price.min is not None:
                query = query.where(Listing.price >= search.price.min)
            if search.price.max is not None:
                query = query.where(Listing.price <= search.price.max)

        if search.area is not None:
            if search.area.min is not None:
                query = query.where(Listing.area >= search.area.min)
            if search.area.max is not None:
                query = query.where(Listing.area <= search.area.max)

        if search.rooms is not None:
            if search.rooms.min is not None:
                query = query.where(Listing.rooms >= int(search.rooms.min))
            if search.rooms.max is not None:
                query = query.where(Listing.rooms <= int(search.rooms.max))

        if search.floor is not None:
            if search.floor.min is not None:
                query = query.where(Listing.floor >= int(search.floor.min))
            if search.floor.max is not None:
                query = query.where(Listing.floor <= int(search.floor.max))

        if search.build_year is not None:
            build_year_expr = cast(Listing.data["build_year"].astext, Integer)
            if search.build_year.min is not None:
                query = query.where(build_year_expr >= int(search.build_year.min))
            if search.build_year.max is not None:
                query = query.where(build_year_expr <= int(search.build_year.max))

        if search.has_repair is not None:
            has_repair_expr = cast(Listing.data["has_repair"].astext, Boolean)
            query = query.where(has_repair_expr.is_(search.has_repair))

        if search.creator_types:
            query = query.where(Listing.data["creator_type"].astext.in_(search.creator_types))

        if search.property_types:
            query = query.where(Listing.data["property_type"].astext.in_(search.property_types))

        if search.living_conditions:
            query = query.where(Listing.data["living_conditions"].contains(search.living_conditions))

        return query

    def list_with_filters(
        self,
        *,
        limit: int,
        offset: int,
        search: ListingSearchDTO,
        sort_by: ListingSortBy | None,
        sort_order: ListingSortOrder | None,
    ) -> tuple[list[Listing], int]:
        base_query = self._apply_filters(select(Listing), search)
        total_query = self._apply_filters(select(func.count(Listing.id)), search)
        total = self.session.scalar(total_query) or 0

        order_by = self._build_ordering(sort_by=sort_by, sort_order=sort_order)
        items_query = (
            base_query.order_by(*order_by)
            .offset(offset)
            .limit(limit)
        )
        items = list(self.session.scalars(items_query))
        return items, total
