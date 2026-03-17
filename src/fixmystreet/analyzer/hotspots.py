"""Hotspot detection for identifying areas with concentrated issues."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fixmystreet.models import Report


@dataclass
class Hotspot:
    """A geographic hotspot with high report density."""

    center_lat: float
    center_lon: float
    report_count: int
    radius_km: float
    report_ids: list[str]
    density_score: float  # 0-1 normalized


class HotspotDetector:
    """Finds geographic areas with high concentrations of reports.

    Uses a grid-based density approach: divides the area into cells,
    counts reports per cell, and identifies cells exceeding a threshold.
    """

    def __init__(self, radius_km: float = 0.5) -> None:
        """Initialize detector.

        Args:
            radius_km: Radius in kilometers for clustering proximity.
        """
        self._radius_km = radius_km
        # Approximate degrees per km at mid-latitudes
        self._deg_per_km_lat = 1.0 / 111.0
        self._deg_per_km_lon = 1.0 / 85.0

    def detect(
        self, reports: list[Report], min_reports: int = 3
    ) -> list[Hotspot]:
        """Detect hotspots from a list of reports.

        Args:
            reports: List of reports to analyze.
            min_reports: Minimum reports in an area to qualify as a hotspot.

        Returns:
            List of Hotspot objects sorted by density score descending.
        """
        if len(reports) < min_reports:
            return []

        clusters = self._cluster_reports(reports)

        hotspots = []
        max_count = max(len(c) for c in clusters.values()) if clusters else 1

        for cell_key, cell_reports in clusters.items():
            if len(cell_reports) >= min_reports:
                lats = [r.location.latitude for r in cell_reports]
                lons = [r.location.longitude for r in cell_reports]
                center_lat = float(np.mean(lats))
                center_lon = float(np.mean(lons))
                density_score = len(cell_reports) / max(max_count, 1)

                hotspot = Hotspot(
                    center_lat=round(center_lat, 6),
                    center_lon=round(center_lon, 6),
                    report_count=len(cell_reports),
                    radius_km=self._radius_km,
                    report_ids=[r.report_id for r in cell_reports],
                    density_score=round(density_score, 3),
                )
                hotspots.append(hotspot)

        hotspots.sort(key=lambda h: h.density_score, reverse=True)
        return hotspots

    def _cluster_reports(
        self, reports: list[Report]
    ) -> dict[tuple[int, int], list[Report]]:
        """Group reports into grid cells based on location."""
        cell_size_lat = self._radius_km * self._deg_per_km_lat
        cell_size_lon = self._radius_km * self._deg_per_km_lon

        clusters: dict[tuple[int, int], list[Report]] = {}

        for report in reports:
            cell_x = int(report.location.latitude / cell_size_lat)
            cell_y = int(report.location.longitude / cell_size_lon)
            key = (cell_x, cell_y)

            if key not in clusters:
                clusters[key] = []
            clusters[key].append(report)

        return clusters

    def compute_density_map(
        self, reports: list[Report], grid_resolution: int = 20
    ) -> np.ndarray:
        """Create a 2D density grid of report locations.

        Args:
            reports: List of reports.
            grid_resolution: Number of cells per axis.

        Returns:
            2D numpy array with report counts per cell.
        """
        if not reports:
            return np.zeros((grid_resolution, grid_resolution))

        lats = np.array([r.location.latitude for r in reports])
        lons = np.array([r.location.longitude for r in reports])

        lat_bins = np.linspace(lats.min(), lats.max() + 1e-9, grid_resolution + 1)
        lon_bins = np.linspace(lons.min(), lons.max() + 1e-9, grid_resolution + 1)

        density, _, _ = np.histogram2d(lats, lons, bins=[lat_bins, lon_bins])
        return density
