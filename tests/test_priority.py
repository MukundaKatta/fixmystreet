"""Tests for priority scorer."""

import pytest

from fixmystreet.models import (
    Issue,
    IssueCategory,
    Location,
    PriorityLevel,
    Report,
)
from fixmystreet.reporter.priority import PriorityScorer


def _make_report(
    report_id: str = "RPT-0001",
    category: IssueCategory = IssueCategory.POTHOLE,
    severity: float = 0.5,
    address: str = "123 Main Street",
    neighborhood: str = "Downtown",
    lat: float = 40.7128,
    lon: float = -74.006,
) -> Report:
    return Report(
        report_id=report_id,
        description="Test report",
        location=Location(
            latitude=lat, longitude=lon,
            address=address, neighborhood=neighborhood,
        ),
        issue=Issue(category=category, severity=severity),
    )


@pytest.fixture
def scorer():
    return PriorityScorer()


class TestPriorityScorer:
    def test_score_returns_float(self, scorer):
        report = _make_report()
        score = scorer.score(report)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_higher_severity_gives_higher_score(self, scorer):
        low = _make_report(report_id="RPT-0001", severity=0.2)
        high = _make_report(report_id="RPT-0002", severity=0.9)
        assert scorer.score(high) > scorer.score(low)

    def test_school_location_increases_score(self, scorer):
        normal = _make_report(report_id="RPT-0001", address="123 Elm Street")
        school = _make_report(report_id="RPT-0002", address="123 School Road")
        assert scorer.score(school) > scorer.score(normal)

    def test_assign_priority_critical(self, scorer):
        report = _make_report(severity=0.95, address="Hospital Drive")
        level = scorer.assign_priority(report)
        assert level in (PriorityLevel.CRITICAL, PriorityLevel.HIGH)
        assert report.priority is not None

    def test_assign_priority_low(self, scorer):
        report = _make_report(
            severity=0.1, category=IssueCategory.GRAFFITI,
            address="456 Quiet Lane", neighborhood="Suburb",
        )
        level = scorer.assign_priority(report)
        assert level in (PriorityLevel.LOW, PriorityLevel.MEDIUM)

    def test_frequency_increases_score(self, scorer):
        # Add multiple reports in same area
        for i in range(5):
            past = _make_report(
                report_id=f"RPT-{i+10:04d}",
                lat=40.7128, lon=-74.006,
            )
            scorer.add_to_history(past)

        report = _make_report(report_id="RPT-0099")
        score_with_history = scorer.score(report)

        fresh_scorer = PriorityScorer()
        score_without = fresh_scorer.score(report)

        assert score_with_history > score_without

    def test_no_issue_still_scores(self, scorer):
        report = Report(
            report_id="RPT-0001",
            description="Unknown issue",
            location=Location(latitude=40.0, longitude=-74.0),
        )
        score = scorer.score(report)
        assert 0.0 <= score <= 1.0
