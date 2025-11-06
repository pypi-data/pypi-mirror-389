"""Package-related helper functions."""

from collections.abc import Iterable
from importlib import metadata
from logging import getLogger

from prometheus_client import Info

logger = getLogger(__name__)


def init_apt_metrics(metrics: Iterable[Info], pkgnames: Iterable[str]) -> None:
    """
    Init Debian package version metrics.

    Args:
        metrics: list of `prometheus_client` Info metrics
        pkgnames: list of APT package names
    """

    try:
        import apt  # pyright: ignore[reportMissingImports] # noqa: PLC0415

    except ImportError:
        logger.error("Unable to import apt module, no package version metrics will be exported.")  # noqa: TRY400
        return

    apt_cache = apt.Cache()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

    for metric, pkgname in zip(metrics, pkgnames, strict=True):
        try:
            package = apt_cache[pkgname]  # pyright: ignore[reportUnknownVariableType]

        except KeyError:
            logger.error("Package name %s is unknown for APT cache, metric %s will not be populated")  # noqa: TRY400
            continue

        # Just in case.
        if not package.installed:  # pyright: ignore[reportUnknownMemberType]
            logger.error("Package %s is not installed, metric %s will not be populated")
            continue

        # Simplification of
        # https://www.debian.org/doc/debian-policy/ch-controlfields.html#version

        version = package.installed.version  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        epoch, revision = "0", ""

        try:
            epoch, rest = version.split(":")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

        except ValueError:
            rest = version  # pyright: ignore[reportUnknownVariableType]

        major, minor, rest = rest.split(".")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        try:
            patchlevel, revision = rest.split("-")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

        except ValueError:
            patchlevel = rest  # pyright: ignore[reportUnknownVariableType]

        info = {  # pyright: ignore[reportUnknownVariableType]
            "pkgname": pkgname,
            "version": version,
            "epoch": epoch,
            "major": major,
            "minor": minor,
            "patchlevel": patchlevel,
            "revision": revision,
        }
        metric.info(val=info)  # pyright: ignore[reportUnknownArgumentType]


def init_pip_metrics(metrics: Iterable[Info], pkgnames: Iterable[str]) -> None:  # pyright: ignore[reportUnknownParameterType]
    """
    Init Pip package version metrics.

    Args:
        metrics: list of `prometheus_client` Info metrics
        pkgnames: list of Pip package names
    """

    for metric, pkgname in zip(metrics, pkgnames, strict=True):
        try:
            major, minor, patchlevel = metadata.version(distribution_name=pkgname).split(".", maxsplit=2)
            info = {"major": major, "minor": minor, "patchlevel": patchlevel}
            metric.info(val=info)

        except metadata.PackageNotFoundError:
            logger.error("Package %s is not is not importable, metric %s will not be populated")  # noqa: TRY400
