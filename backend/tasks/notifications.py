from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.core.celery_app import celery_app
from backend.core.config import settings
from backend.db.session import SessionLocal
from backend.logging_utils import log_exception, log_info
from backend.services.notification_pipeline import (
    match_listings_to_subscriptions,
    materialize_pending_deliveries,
    process_pending_deliveries,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="notifications.match_listings_task")
def match_listings_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        log_info(
            logger, "Notifications match task started", event="notifications.task_started",
            task="notifications.match_listings_task", task_id=self.request.id, user_id=user_id
        )
        created = match_listings_to_subscriptions(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        payload = {"created_notifications": created, "user_id": user_id}
        log_info(
            logger, "Notifications match task finished", event="notifications.task_finished",
            task="notifications.match_listings_task", task_id=self.request.id, **payload
        )
        return payload
    except Exception:
        log_exception(
            logger, "Notifications match task failed", event="notifications.task_failed",
            task="notifications.match_listings_task", task_id=self.request.id, user_id=user_id
        )
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="notifications.materialize_deliveries_task")
def materialize_deliveries_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        log_info(
            logger, "Notifications materialize task started", event="notifications.task_started",
            task="notifications.materialize_deliveries_task", task_id=self.request.id, user_id=user_id
        )
        created = materialize_pending_deliveries(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        payload = {"created_deliveries": created, "user_id": user_id}
        log_info(
            logger, "Notifications materialize task finished", event="notifications.task_finished",
            task="notifications.materialize_deliveries_task", task_id=self.request.id, **payload
        )
        return payload
    except Exception:
        log_exception(
            logger, "Notifications materialize task failed", event="notifications.task_failed",
            task="notifications.materialize_deliveries_task", task_id=self.request.id, user_id=user_id
        )
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="notifications.process_deliveries_task")
def process_deliveries_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        log_info(
            logger, "Notifications process task started", event="notifications.task_started",
            task="notifications.process_deliveries_task", task_id=self.request.id, user_id=user_id
        )
        processed = process_pending_deliveries(
            db,
            batch_size=settings.NOTIFICATIONS_MATCHER_BATCH_SIZE,
            user_id=user_id,
        )
        payload = {"processed_deliveries": processed, "user_id": user_id}
        log_info(
            logger, "Notifications process task finished", event="notifications.task_finished",
            task="notifications.process_deliveries_task", task_id=self.request.id, **payload
        )
        return payload
    except Exception:
        log_exception(
            logger, "Notifications process task failed", event="notifications.task_failed",
            task="notifications.process_deliveries_task", task_id=self.request.id, user_id=user_id
        )
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="notifications.run_full_pipeline_task")
def run_full_pipeline_task(self, user_id: int | None = None) -> dict:
    db: Session = SessionLocal()
    try:
        log_info(
            logger, "Notifications full pipeline task started", event="notifications.task_started",
            task="notifications.run_full_pipeline_task", task_id=self.request.id, user_id=user_id
        )
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
        payload = {
            "created_notifications": created_notifications,
            "created_deliveries": created_deliveries,
            "processed_deliveries": processed_deliveries,
            "user_id": user_id,
        }
        log_info(
            logger, "Notifications full pipeline task finished", event="notifications.task_finished",
            task="notifications.run_full_pipeline_task", task_id=self.request.id, **payload
        )
        return payload
    except Exception:
        log_exception(
            logger, "Notifications full pipeline task failed", event="notifications.task_failed",
            task="notifications.run_full_pipeline_task", task_id=self.request.id, user_id=user_id
        )
        db.rollback()
        raise
    finally:
        db.close()
