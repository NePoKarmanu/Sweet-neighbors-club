#!/bin/sh
set -e

exec celery -A backend.core.celery_app.celery_app worker -l "${CELERY_LOG_LEVEL:-WARNING}"
