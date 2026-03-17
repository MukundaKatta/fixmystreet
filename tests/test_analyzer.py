"""Tests for analyzer modules."""

from datetime import datetime, timedelta

import numpy as np
import pytest

from fixmystreet.analyzer.hotspots import HotspotDetector
from fixmystreet.analyzer.response import ResponseTimeAnalyzer
from fixmystreet.analyzer.trends import TrendAnalyzer
from fixmystreet.models import (
    Issue,
    IssueCategory,
    Location,
    PriorityLevel,
    Report,
    ReportStatus,
    Resolution,
)


def _make_report(
    report_id: str,
    lat: float = 40.7128,
    lon: float = -74.006,
    category: IssueCategory = IssueCategory.POTHOLE,
    status: ReportStatus = ReportStatus.REPORTED,
    days_ago: float = 0,
    resolution_hours: float | None = None,
) -> Report:
    reported_at = datetime.now() - timedelta(days=days_ago)
    resolution = None
    resolved_at = None
    ack_at = None
    priority = PriorityLevel.MEDIUM

    if status in (ReportStatus.ACKNOWLEDGED, ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED):
        ack_at = reported_at + timedelta(hours=2)

    if resolution_hours is not None and status == ReportStatus.RESOLVED:
        resolved_at = reported_at + timedelta(hours=resolution_hours)
        resolution = Resolution(
            resolved_at=resolved_at,
            resolution_time_hours=resolution_hours,
            resolution_notes="Resolved.",
        )

    return Report(
        report_id=report_id,
        description="Test",
        location=Location(latitude=lat, longitude=lon, neighborhood="Test Area"),
        issue=Issue(category=category, severity=0.5),
        status=status,
        priority=priority,
        reported_at=reported_at,
        acknowledged_at=ack_at,
        resolved_at=resolved_at,
        resolution=resolution,
    )


class TestHotspotDetector:
    def test_detect_no_reports(self):
        detector = HotspotDetector()
        assert detector.detect([]) == []

    def test_detect_too_few_reports(self):
        reports = [_make_report(f"RPT-{i:04d}") for i in range(2)]
        detector = HotspotDetector()
        assert detector.detect(reports, min_reports=3) == []

    def test_detect_cluster(self):
        # Create a cluster of reports in the same area
        reports = [
            _make_report(f"RPT-{i:04d}", lat=40.7128 + 0.001 * i, lon=-74.006)
            for i in range(5)
        ]
        detector = HotspotDetector(radius_km=1.0)
        hotspots = detector.detect(reports, min_reports=3)
        assert len(hotspots) >= 1
        assert hotspots[0].report_count >= 3

    def test_density_map(self):
        reports = [
            _make_report(f"RPT-{i:04d}", lat=40.7 + 0.01 * i, lon=-74.0)
            for i in range(10)
        ]
        detector = HotspotDetector()
        density = detector.compute_density_map(reports, grid_resolution=5)
        assert density.shape == (5, 5)
        assert density.sum() == 10

    def test_density_map_empty(self):
        detector = HotspotDetector()
        density = detector.compute_density_map([], grid_resolution=10)
        assert density.shape == (10, 10)
        assert density.sum() == 0


class TestTrendAnalyzer:
    def test_analyze_empty(self):
        analyzer = TrendAnalyzer()
        summary = analyzer.analyze([])
        assert summary.total_reports == 0

    def test_analyze_with_reports(self):
        reports = [
            _make_report(f"RPT-{i:04d}", days_ago=i * 2, category=IssueCategory.POTHOLE)
            for i in range(20)
        ]
        analyzer = TrendAnalyzer()
        summary = analyzer.analyze(reports, period_days=7)
        assert summary.total_reports == 20
        assert summary.most_common_category == "pothole"

    def test_category_breakdown(self):
        reports = [
            _make_report("RPT-0001", category=IssueCategory.POTHOLE),
            _make_report("RPT-0002", category=IssueCategory.POTHOLE),
            _make_report("RPT-0003", category=IssueCategory.GRAFFITI),
        ]
        analyzer = TrendAnalyzer()
        breakdown = analyzer.category_breakdown(reports)
        assert breakdown["pothole"] == 2
        assert breakdown["graffiti"] == 1
        assert breakdown["flooding"] == 0

    def test_daily_volume(self):
        now = datetime.now()
        reports = [
            _make_report(f"RPT-{i:04d}", days_ago=0)
            for i in range(5)
        ]
        analyzer = TrendAnalyzer()
        volume = analyzer.daily_volume(reports, days=7)
        assert sum(volume.values()) == 5


class TestResponseTimeAnalyzer:
    def test_analyze_empty(self):
        analyzer = ResponseTimeAnalyzer()
        metrics = analyzer.analyze([])
        assert metrics.total_resolved == 0
        assert metrics.avg_response_hours == 0.0

    def test_analyze_resolved_reports(self):
        reports = [
            _make_report(
                f"RPT-{i:04d}",
                status=ReportStatus.RESOLVED,
                resolution_hours=float(24 + i * 12),
                days_ago=10,
            )
            for i in range(5)
        ]
        analyzer = ResponseTimeAnalyzer()
        metrics = analyzer.analyze(reports)
        assert metrics.total_resolved == 5
        assert metrics.avg_response_hours > 0
        assert metrics.median_response_hours > 0

    def test_on_time_percentage(self):
        # All resolved within medium target (168 hours)
        reports = [
            _make_report(
                f"RPT-{i:04d}",
                status=ReportStatus.RESOLVED,
                resolution_hours=48.0,
                days_ago=30,
            )
            for i in range(3)
        ]
        analyzer = ResponseTimeAnalyzer()
        metrics = analyzer.analyze(reports)
        assert metrics.on_time_percent == 100.0

    def test_overdue_reports(self):
        reports = [
            _make_report("RPT-0001", days_ago=30, status=ReportStatus.IN_PROGRESS),
        ]
        analyzer = ResponseTimeAnalyzer()
        overdue = analyzer.get_overdue_reports(reports)
        assert len(overdue) == 1

    def test_by_category(self):
        reports = [
            _make_report(
                "RPT-0001",
                category=IssueCategory.POTHOLE,
                status=ReportStatus.RESOLVED,
                resolution_hours=48.0,
                days_ago=10,
            ),
            _make_report(
                "RPT-0002",
                category=IssueCategory.GRAFFITI,
                status=ReportStatus.RESOLVED,
                resolution_hours=72.0,
                days_ago=10,
            ),
        ]
        analyzer = ResponseTimeAnalyzer()
        metrics = analyzer.analyze(reports)
        assert "pothole" in metrics.by_category
        assert "graffiti" in metrics.by_category
