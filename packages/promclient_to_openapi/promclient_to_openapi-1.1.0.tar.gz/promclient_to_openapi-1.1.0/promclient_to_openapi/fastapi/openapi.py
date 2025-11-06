"""Helper for OpenAPI schema modification."""

from functools import partial
from typing import Any

from fastapi import FastAPI


def extended_openapi(app: FastAPI, schema: dict[str, Any]) -> dict[str, Any]:
    """
    Modify default OpenAPI spec for metrics to be documented.

    Args:
        app: FastAPI instance.
        schema: Generated metrics schema

    Returns:
        New OpenAPI schema.
    """

    # This should be called only once, obviously.
    if app.openapi_schema:
        return app.openapi_schema

    # Get .default_openapi() which is set by lifespan hook and update it.
    openapi_schema: dict[str, Any] = app.default_openapi()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]
    openapi_schema["components"]["schemas"].update(schema)  # pyright: ignore[reportUnknownMemberType]

    # FastAPI inserts "type" parameter here so ReDoc cannot handle custom schema
    # reference. This content_type is defined in
    # tileserver.internal.metrics_handler.MetricsResponse class.
    del openapi_schema["paths"]["/metrics"]["get"]["responses"]["200"]["content"]["application/openmetrics-text"]["schema"]["type"]

    # Also remove default 422 Validation Error from documentation since there is
    # no actual validation of Accept header, just some kind of negotiation to
    # support "Accept: application/openmetrics-text".
    del openapi_schema["paths"]["/metrics"]["get"]["responses"]["422"]

    app.openapi_schema = openapi_schema
    return openapi_schema  # pyright: ignore[reportUnknownVariableType]


def setup_metrics(app: FastAPI) -> None:
    """
    Set hook for OpenAPI spec call to be owerriden by ours.

    Use in lifespan contentmanager on FastAPI application startup.

    Args:
        app: FastAPI instance.
    """

    app.default_openapi = app.openapi  # pyright: ignore[reportAttributeAccessIssue]
    app.openapi = partial(extended_openapi, app)  # pyright: ignore[reportAttributeAccessIssue]
