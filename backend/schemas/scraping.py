from __future__ import annotations

from pydantic import BaseModel


class ScrapingRunResponse(BaseModel):
    task_id: str
    provider: str | None
    mode: str


class ScrapingTaskStatusResponse(BaseModel):
    task_id: str
    state: str
    result: dict | None
