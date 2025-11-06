"""Helpers for integration with FastAPI."""

from fastapi import status
from fastapi.responses import JSONResponse

from .models import HealthyModel, OpenMetricsResponse, PlainMetricsResponse, ReadyModel, UnhealthyModel
from .openapi import setup_metrics

__all__ = ("HealthyModel", "OpenMetricsResponse", "PlainMetricsResponse", "ReadyModel", "UnhealthyModel", "setup_metrics")


def ready() -> JSONResponse:
    """Return plain `200 OK` to indicate what server started."""  # noqa: DOC201

    return JSONResponse(content=ReadyModel(), status_code=status.HTTP_200_OK)
