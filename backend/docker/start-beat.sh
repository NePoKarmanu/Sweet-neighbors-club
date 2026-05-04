#!/bin/sh
set -e

exec celery -A backend.core.celery_app.celery_app beat -l "${CELERY_LOG_LEVEL:-WARNING}"
