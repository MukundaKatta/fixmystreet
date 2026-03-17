"""Tests for data models."""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from fixmystreet.models import (
    Issue,
    IssueCategory,
    Location,
    PriorityLevel,
    Report,
    ReportStatus,
    Resolution,
)


class TestLocation:
    def test_create_location(self):
        loc = Location(latitude=40.7128, longitude=-74.0060, address="123 Main St")
        assert loc.latitude == 40.7128
        assert loc.longitude == -74.0060
        assert loc.address == "123 Main St"

    def test_coordinates_property(self):
        loc = Location(latitude=40.0, longitude=-74.0)
        assert loc.coordinates == (40.0, -74.0)

    def test_invalid_latitude(self):
        with pytest.raises(ValidationError):
            Location(latitude=91.0, longitude=0.0)

    def test_invalid_longitude(self):
        with pytest.raises(ValidationError):
            Location(latitude=0.0, longitude=181.0)


class TestIssue:
    def test_create_issue(self):
        issue = Issue(category=IssueCategory.POTHOLE, severity=0.8)
        assert issue.category == IssueCategory.POTHOLE
        assert issue.severity == 0.8
        assert issue.confidence == 1.0

    def test_default_values(self):
        issue = Issue(category=IssueCategory.GRAFFITI)
        assert issue.confidence == 1.0
        assert issue.severity == 0.5
        assert issue.description == ""

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            Issue(category=IssueCategory.POTHOLE, severity=1.5)


class TestResolution:
    def test_create_resolution(self):
        now = datetime.now()
        res = Resolution(
            resolved_at=now,
            resolution_notes="Fixed",
            resolution_time_hours=48.0,
        )
        assert res.resolved_at == now
        assert res.resolution_time_hours == 48.0

    def test_default_values(self):
        res = Resolution(resolved_at=datetime.now())
        assert res.resolution_notes == ""
        assert res.cost_estimate is None
        assert res.crew_size == 1


class TestReport:
    def test_create_report(self):
        report = Report(
            report_id="RPT-0001",
            description="A pothole",
            location=Location(latitude=40.0, longitude=-74.0),
        )
        assert report.report_id == "RPT-0001"
        assert report.status == ReportStatus.REPORTED
        assert report.priority is None

    def test_invalid_report_id(self):
        with pytest.raises(ValidationError):
            Report(
                report_id="INVALID",
                description="test",
                location=Location(latitude=0, longitude=0),
            )

    def test_is_resolved(self):
        report = Report(
            report_id="RPT-0001",
            description="test",
            location=Location(latitude=0, longitude=0),
            status=ReportStatus.RESOLVED,
        )
        assert report.is_resolved is True

    def test_not_resolved(self):
        report = Report(
            report_id="RPT-0001",
            description="test",
            location=Location(latitude=0, longitude=0),
        )
        assert report.is_resolved is False

    def test_age_hours(self):
        report = Report(
            report_id="RPT-0001",
            description="test",
            location=Location(latitude=0, longitude=0),
            reported_at=datetime.now() - timedelta(hours=5),
        )
        assert 4.9 < report.age_hours < 5.1

    def test_all_categories_exist(self):
        expected = {
            "pothole", "broken_light", "graffiti", "damaged_sign",
            "flooding", "sidewalk_crack", "fallen_tree", "illegal_dumping",
        }
        actual = {c.value for c in IssueCategory}
        assert actual == expected

    def test_all_statuses_exist(self):
        expected = {"reported", "acknowledged", "in_progress", "resolved"}
        actual = {s.value for s in ReportStatus}
        assert actual == expected
