from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.celery_app import celery_app
from backend.core.config import settings
from backend.db.session import SessionLocal
from backend.services.notification_pipeline import (
    match_listings_to_subscriptions,
    materialize_pending_deliveries,
    process_pending_deliveries,
)


@celery_app.task(bind=True, name="notifications.match_listings_task")
def match_listings_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        created = match_listings_to_subscriptions(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        return {"created_notifications": created, "user_id": user_id}
    finally:
        db.close()


@celery_app.task(bind=True, name="notifications.materialize_deliveries_task")
def materialize_deliveries_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        created = materialize_pending_deliveries(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        return {"created_deliveries": created, "user_id": user_id}
    finally:
        db.close()


@celery_app.task(bind=True, name="notifications.process_deliveries_task")
def process_deliveries_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        processed = process_pending_deliveries(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        return {"processed_deliveries": processed, "user_id": user_id}
    finally:
        db.close()


@celery_app.task(bind=True, name="notifications.run_full_pipeline_task")
def run_full_pipeline_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        created_notifications = match_listings_to_subscriptions(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        created_deliveries = materialize_pending_deliveries(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        processed_deliveries = process_pending_deliveries(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        return {
            "created_notifications": created_notifications,
            "created_deliveries": created_deliveries,
            "processed_deliveries": processed_deliveries,
            "user_id": user_id,
        }
    finally:
        db.close()
