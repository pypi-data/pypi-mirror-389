"""Helper classes for FastAPI integration."""

from fastapi import Response
from prometheus_client.exposition import generate_latest as generate_plain
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from prometheus_client.openmetrics.exposition import generate_latest as generate_openmetrics  # pyright: ignore[reportUnknownVariableType]
from prometheus_client.registry import CollectorRegistry
from pydantic import BaseModel, Field


class PlainMetricsResponse(Response):
    """Plain Prometheus metrics response."""

    media_type = "text/plain"

    def render(self, content: CollectorRegistry) -> bytes:  # noqa: D102, PLR6301
        return generate_plain(registry=content)


class OpenMetricsResponse(Response):
    """Strict OpenMetrics response."""

    media_type = CONTENT_TYPE_LATEST

    def render(self, content: CollectorRegistry) -> bytes:  # noqa: D102, PLR6301
        return generate_openmetrics(registry=content)  # pyright: ignore[reportUnknownVariableType]


class ReadyModel(BaseModel):
    """Model of ready state, only for docs."""

    detail: str = Field(default="Ready", description="Application is ready to receive requests.")


class HealthyModel(BaseModel):
    """Model of healty state, only for docs."""

    detail: str = Field(default="Healthy", description="Current application state.")


class UnhealthyModel(BaseModel):
    """Model of unhealty state, only for docs."""

    detail: str = Field(default="Unhealthy", description="Current application state.")
