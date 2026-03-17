"""Tests for issue tracker."""

import pytest

from fixmystreet.models import Location, Report, ReportStatus
from fixmystreet.reporter.tracker import (
    InvalidTransitionError,
    IssueTracker,
    ReportNotFoundError,
)


def _make_report(report_id: str = "RPT-0001") -> Report:
    return Report(
        report_id=report_id,
        description="Test issue",
        location=Location(latitude=40.0, longitude=-74.0),
    )


@pytest.fixture
def tracker():
    t = IssueTracker()
    t.add_report(_make_report("RPT-0001"))
    t.add_report(_make_report("RPT-0002"))
    return t


class TestIssueTracker:
    def test_add_and_get_report(self, tracker):
        report = tracker.get_report("RPT-0001")
        assert report.report_id == "RPT-0001"

    def test_get_nonexistent_report(self, tracker):
        with pytest.raises(ReportNotFoundError):
            tracker.get_report("RPT-9999")

    def test_transition_to_acknowledged(self, tracker):
        report = tracker.transition("RPT-0001", ReportStatus.ACKNOWLEDGED)
        assert report.status == ReportStatus.ACKNOWLEDGED
        assert report.acknowledged_at is not None

    def test_transition_to_in_progress(self, tracker):
        tracker.transition("RPT-0001", ReportStatus.ACKNOWLEDGED)
        report = tracker.transition("RPT-0001", ReportStatus.IN_PROGRESS)
        assert report.status == ReportStatus.IN_PROGRESS

    def test_transition_to_resolved(self, tracker):
        tracker.transition("RPT-0001", ReportStatus.ACKNOWLEDGED)
        tracker.transition("RPT-0001", ReportStatus.IN_PROGRESS)
        report = tracker.transition(
            "RPT-0001", ReportStatus.RESOLVED, resolution_notes="Fixed it"
        )
        assert report.status == ReportStatus.RESOLVED
        assert report.resolution is not None
        assert report.resolution.resolution_notes == "Fixed it"

    def test_invalid_transition(self, tracker):
        with pytest.raises(InvalidTransitionError):
            tracker.transition("RPT-0001", ReportStatus.RESOLVED)

    def test_cannot_transition_from_resolved(self, tracker):
        tracker.transition("RPT-0001", ReportStatus.ACKNOWLEDGED)
        tracker.transition("RPT-0001", ReportStatus.IN_PROGRESS)
        tracker.transition("RPT-0001", ReportStatus.RESOLVED)
        with pytest.raises(InvalidTransitionError):
            tracker.transition("RPT-0001", ReportStatus.REPORTED)

    def test_get_reports_by_status(self, tracker):
        tracker.transition("RPT-0001", ReportStatus.ACKNOWLEDGED)
        reported = tracker.get_reports_by_status(ReportStatus.REPORTED)
        acknowledged = tracker.get_reports_by_status(ReportStatus.ACKNOWLEDGED)
        assert len(reported) == 1
        assert len(acknowledged) == 1

    def test_get_all_reports(self, tracker):
        assert len(tracker.get_all_reports()) == 2

    def test_get_open_reports(self, tracker):
        assert len(tracker.get_open_reports()) == 2
        tracker.transition("RPT-0001", ReportStatus.ACKNOWLEDGED)
        tracker.transition("RPT-0001", ReportStatus.IN_PROGRESS)
        tracker.transition("RPT-0001", ReportStatus.RESOLVED)
        assert len(tracker.get_open_reports()) == 1

    def test_get_stats(self, tracker):
        stats = tracker.get_stats()
        assert stats["total"] == 2
        assert stats["reported"] == 2

    def test_total_reports(self, tracker):
        assert tracker.total_reports == 2

    def test_search_by_status(self, tracker):
        results = tracker.search(status=ReportStatus.REPORTED)
        assert len(results) == 2
