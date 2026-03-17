"""Tests for report simulator."""

import pytest

from fixmystreet.models import IssueCategory, ReportStatus
from fixmystreet.simulator import ReportSimulator


class TestReportSimulator:
    def test_generate_reports(self):
        sim = ReportSimulator(seed=42)
        reports = sim.generate(count=20)
        assert len(reports) == 20

    def test_reports_have_valid_ids(self):
        sim = ReportSimulator(seed=42)
        reports = sim.generate(count=5)
        for report in reports:
            assert report.report_id.startswith("RPT-")

    def test_reports_have_issues(self):
        sim = ReportSimulator(seed=42)
        reports = sim.generate(count=10)
        for report in reports:
            assert report.issue is not None
            assert report.issue.category in IssueCategory

    def test_reports_have_locations(self):
        sim = ReportSimulator(seed=42)
        reports = sim.generate(count=10)
        for report in reports:
            assert -90 <= report.location.latitude <= 90
            assert -180 <= report.location.longitude <= 180
            assert report.location.neighborhood != ""

    def test_reports_have_varied_statuses(self):
        sim = ReportSimulator(seed=42)
        reports = sim.generate(count=100, days_back=180)
        statuses = {r.status for r in reports}
        # With 100 reports over 180 days, we should see multiple statuses
        assert len(statuses) >= 2

    def test_seed_reproducibility(self):
        sim1 = ReportSimulator(seed=123)
        sim2 = ReportSimulator(seed=123)
        r1 = sim1.generate(count=5)
        r2 = sim2.generate(count=5)
        for a, b in zip(r1, r2):
            assert a.report_id == b.report_id
            assert a.issue.category == b.issue.category
            assert a.location.neighborhood == b.location.neighborhood

    def test_resolved_reports_have_resolution(self):
        sim = ReportSimulator(seed=42)
        reports = sim.generate(count=100, days_back=180)
        resolved = [r for r in reports if r.status == ReportStatus.RESOLVED]
        for r in resolved:
            assert r.resolution is not None
            assert r.resolution.resolution_time_hours > 0

    def test_custom_center_location(self):
        sim = ReportSimulator(center_lat=51.5074, center_lon=-0.1278, seed=42)
        reports = sim.generate(count=10)
        for report in reports:
            assert abs(report.location.latitude - 51.5074) < 0.1
            assert abs(report.location.longitude - (-0.1278)) < 0.1
